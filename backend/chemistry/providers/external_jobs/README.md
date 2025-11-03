"""
README para providers de procesos externos pesados (ejemplo: TEST, Ambit, simulaciones).

Incluye:

- Descripción de la arquitectura (interfaces, transactional outbox, worker, telemetría)
- Ejemplo de uso
- Alternativa Temporal/Cadence (no implementada, documentada)
- Seguridad: integración con vault/secret manager (documentado)
- Checklist de robustez
  """

# External Job Providers (Durable, Resumable, Observable)

## Arquitectura

- **Interfaces tipadas**: `ExternalJobProvider` define start/resume/status/cancel/heartbeat.
- **Durabilidad**: modelos `Execution`, `Checkpoint`, `OutboxEntry` (transactional outbox).
- **Worker supervisor**: Dramatiq (o RQ) ejecuta jobs en segundo plano, con reintentos, backoff, circuit-breaker.
- **Observabilidad**: endpoints health/metrics, logs estructurados.
- **Idempotencia**: execution_id (UUID) + idempotency_key.
- **Checkpoints**: persistidos y versionados.

## Ejemplo de uso

```python
from chemistry.providers.external_jobs.interfaces import ExternalJobProvider
from chemistry.providers.external_jobs.models import Execution

# Crear ejecución
execution = Execution.objects.create(...)
# Lanzar worker
from chemistry.providers.external_jobs.worker import run_external_job
run_external_job.send(str(execution.execution_id))
```

## Alternativa Temporal/Cadence

- Para tareas de meses, usar Temporal/Cadence (workflow engine durable, reintentos, timers, signals, queries, etc.).
- Integración: definir workflow y activities tipadas, usar Temporal Python SDK.
- No implementado aquí por simplicidad, pero recomendado para cargas críticas.

## Seguridad

- No almacenar secretos en texto plano.
- Integrar con HashiCorp Vault, AWS Secrets Manager, etc. (ver docstrings para hooks de integración).

## Checklist de robustez

- [x] Interfaces tipadas (sin # type: ignore)
- [x] Checkpoints versionados
- [x] Transactional outbox
- [x] Reintentos y backoff
- [x] Circuit-breaker
- [x] Telemetría y health
- [x] Tests unitarios/integración
- [x] Idempotencia
- [x] Documentación de alternativa Temporal/Cadence
- [x] Seguridad documentada

## Recuperación manual

- Si un job queda en estado WAITING_RESUME o BROKEN, puede reanudarse manualmente desde el último checkpoint usando la interfaz de admin o scripts.
