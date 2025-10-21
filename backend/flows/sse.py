"""
Servicio SSE (Server-Sent Events) para logs de ejecución de steps.

Provee un broker en memoria para publicar y suscribirse a eventos de logs
por cada StepExecution. El objetivo es permitir al frontend escuchar en
tiempo real las salidas de los steps vía EventSource.

Notas:
- Este broker es en memoria y por proceso. En producción con múltiples
  réplicas/worker processes, considera Redis Pub/Sub u otro backend
  compartido.
- Incluye heartbeats periódicos para mantener viva la conexión.

Uso desde frontend (Angular/TS):

    const src = new EventSource(`/api/flows/step-executions/${stepExecId}/logs/stream/`);
    src.onmessage = (e) => {
        // e.data es un JSON: { event, data }
        const msg = JSON.parse(e.data);
        if (msg.event === 'log') {
            console.log(msg.data.line);
        }
    };
    src.addEventListener('end', () => src.close());
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from queue import Empty, Queue
from typing import Dict, Generator, List
from uuid import UUID

HEARTBEAT_INTERVAL_SECONDS = 15


@dataclass
class _Subscriber:
    queue: Queue
    created_at: float


class StepLogBroker:
    """
    Broker en memoria para distribución de logs por StepExecution.

    Estructura:
      - subscribers: dict[step_execution_id] -> list[_Subscriber]
    """

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[_Subscriber]] = {}
        self._lock = threading.Lock()

    def _key(self, step_execution_id: UUID | str) -> str:
        return str(step_execution_id)

    def subscribe(self, step_execution_id: UUID | str) -> Queue:
        """Crea una suscripción (cola) para un StepExecution y la devuelve."""
        q: Queue = Queue(maxsize=1000)
        sub = _Subscriber(queue=q, created_at=time.time())
        key = self._key(step_execution_id)
        with self._lock:
            self._subscribers.setdefault(key, []).append(sub)
        return q

    def unsubscribe(self, step_execution_id: UUID | str, q: Queue) -> None:
        key = self._key(step_execution_id)
        with self._lock:
            if key in self._subscribers:
                self._subscribers[key] = [
                    s for s in self._subscribers[key] if s.queue is not q
                ]
                if not self._subscribers[key]:
                    self._subscribers.pop(key, None)

    def publish(self, step_execution_id: UUID | str, event: str, data: dict) -> None:
        """Publica un evento a todos los suscriptores de un StepExecution."""
        message = {
            "event": event,
            "data": data,
        }
        payload = json.dumps(message, ensure_ascii=False)
        key = self._key(step_execution_id)
        with self._lock:
            for sub in self._subscribers.get(key, []):
                try:
                    sub.queue.put_nowait(payload)
                except Exception:
                    # Si la cola está llena o falla, ignoramos para no bloquear
                    pass

    def complete(self, step_execution_id: UUID | str) -> None:
        """Notifica cierre del stream para los suscriptores de un StepExecution."""
        self.publish(step_execution_id, event="end", data={"message": "completed"})

    def stream(self, step_execution_id: UUID | str) -> Generator[str, None, None]:
        """
        Generador de SSE para un StepExecution.

        Produce heartbeats si no hay eventos por HEARTBEAT_INTERVAL_SECONDS.
        """
        q = self.subscribe(step_execution_id)
        try:
            while True:
                try:
                    item = q.get(timeout=HEARTBEAT_INTERVAL_SECONDS)
                    yield self._format_sse(item)
                except Empty:
                    # Heartbeat como comentario SSE
                    yield ": keep-alive\n\n"
        except GeneratorExit:
            # Cliente cerró conexión
            pass
        finally:
            self.unsubscribe(step_execution_id, q)

    @staticmethod
    def _format_sse(json_payload: str) -> str:
        """
        Formatea un payload (JSON) al formato SSE (data: ...\n\n).

        El payload ya incluye event y data serializados.
        """
        return f"data: {json_payload}\n\n"


# Instancia global del broker
step_log_broker = StepLogBroker()
