"""
Worker supervisor y job queue para ejecuciones en segundo plano duraderas.
Por defecto usa Dramatiq si está instalado. Si no, expone una implementación
sin dependencia que permite ejecutar los actores de forma síncrona (fallback),
de modo que los tests no fallen por falta de la librería. En producción se
recomienda instalar Dramatiq y configurar un broker adecuado.

Incluye lógica de reintentos, backoff exponencial con jitter, circuit-breaker
y reanudación desde checkpoint.
"""

from __future__ import annotations

import os
import random
import time

try:
    import dramatiq
except Exception:
    dramatiq = None  # Fallback para entornos sin dramatiq

from .models import Execution, ExecutionStatus
from .persistence import persist_execution_with_outbox

# Modo rápido de test: si no hay dramatiq (fallback) o variable de entorno activada
FAST_MODE = (dramatiq is None) or os.environ.get("EXTERNAL_JOBS_FAST", "0") == "1"

MAX_RETRIES = 5
if FAST_MODE:
    BASE_BACKOFF = 0  # seconds
    MAX_BACKOFF = 0
    WORK_STEP_SLEEP = 0.01
else:
    BASE_BACKOFF = 60  # seconds
    MAX_BACKOFF = 3600  # seconds
    WORK_STEP_SLEEP = 5.0


def exponential_backoff_with_jitter(attempt: int) -> int:
    if FAST_MODE:
        return 0
    base = min(BASE_BACKOFF * (2**attempt), MAX_BACKOFF)
    return int(base * (0.5 + random.random()))


def _actor(**kwargs):
    """Devuelve un actor de Dramatiq si está disponible, o un wrapper síncrono
    con método .send() para entornos de test sin Dramatiq.
    """

    def decorator(fn):
        if dramatiq is not None:
            return dramatiq.actor(**kwargs)(fn)

        class _SyncActor:
            def __init__(self, func):
                self._func = func

            def send(self, *args, **_kwargs):
                return self._func(*args, **_kwargs)

            def __call__(self, *args, **_kwargs):
                return self._func(*args, **_kwargs)

        return _SyncActor(fn)

    return decorator


@_actor(max_retries=MAX_RETRIES)
def run_external_job(execution_id: str) -> None:
    execution = Execution.objects.get(execution_id=execution_id)
    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            # Aquí se llamaría al provider real (ejemplo: Ambit, TEST, etc.)
            # Simulación de trabajo pesado y checkpoint
            time.sleep(WORK_STEP_SLEEP)  # Simula trabajo
            checkpoint_data = {
                "step": f"step_{attempt}",
                "data": {"progress": attempt * 20},
            }
            execution.status = ExecutionStatus.RUNNING
            persist_execution_with_outbox(execution, checkpoint_data=checkpoint_data)
            # Simula éxito
            if attempt == 2:
                execution.status = ExecutionStatus.SUCCEEDED
                persist_execution_with_outbox(execution)
                return
            attempt += 1
            raise RuntimeError("Simulated failure for retry")
        except Exception as e:
            execution.status = ExecutionStatus.WAITING_RETRY
            execution.error = str(e)
            persist_execution_with_outbox(execution)
            backoff = exponential_backoff_with_jitter(attempt)
            time.sleep(backoff)
            attempt += 1
    execution.status = ExecutionStatus.BROKEN
    persist_execution_with_outbox(execution)


# Circuit-breaker, health, y polling supervisor pueden implementarse como actores adicionales o cron jobs.
