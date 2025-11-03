"""
Módulo de telemetría y health checks para providers de procesos pesados.
Expone métricas Prometheus, health/readiness y logs estructurados.
"""

from __future__ import annotations

from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET

from .models import Execution


@require_GET
def health_check(request):
    """Endpoint de health check básico."""
    return JsonResponse({"status": "ok"})


@require_GET
def readiness_check(request):
    """Endpoint de readiness (¿hay workers activos?)."""
    # Aquí se podría consultar el estado de Dramatiq/RQ
    return JsonResponse({"ready": True})


@require_GET
def metrics(request):
    """Métricas estilo Prometheus para ejecuciones."""
    counts = (
        Execution.objects.values("status").annotate(count=Count("status")).order_by()
    )
    lines = [
        f'external_job_executions_total{{status="{row["status"]}"}} {row["count"]}'
        for row in counts
    ]
    content = "\n".join(lines) + "\n"
    return HttpResponse(content, content_type="text/plain; version=0.0.4")
