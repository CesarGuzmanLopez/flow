"""
Vistas (ViewSets) de la aplicación de flujos de trabajo.

Define los endpoints REST API para:
- Gestión de flujos (CRUD, acciones personalizadas)
- Versiones de flujos
- Pasos (steps) de flujos
- Artefactos (artifacts) asociados a pasos
- Ejecuciones (snapshots y step executions)
- Ramas (branches) de flujos con sistema de árbol sin merges
- Nodos (nodes) para visualización del árbol

Implementa control de acceso basado en propiedad y permisos de usuario.
"""

from back.envelope import StandardEnvelopeMixin
from django.db import models
from django.http import Http404, StreamingHttpResponse
from django.utils.timezone import now
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from users.permissions import HasAppPermission

from . import services as flow_services
from .domain.flujo import predefined_cadma  # noqa: F401 - ensure registration
from .domain.flujo.builder import create_flow_from_definition
from .domain.flujo.definitions import get_definition, list_definitions
from .domain.services import FlowExecutionService, FlowPermissionService
from .domain.steps import (  # noqa: F401
    create_reference_family,  # side-effect: register step
    create_reference_molecule_family,  # side-effect: register step
    generate_admetsa_family_aggregates,  # noqa: F401 - side-effect import
    generate_admetsa_properties,  # side-effect: register step
    generate_substitution_permutations_family,  # noqa: F401 - side-effect import
)
from .domain.steps.interface import (
    DataStack,
    StepContext,
    execute_step,
    list_step_specs,
)
from .models import (
    Artifact,
    ExecutionSnapshot,
    Flow,
    FlowBranch,
    FlowNode,
    FlowVersion,
    Step,
    StepExecution,
)
from .serializers import (
    ArtifactSerializer,
    ExecutionSnapshotSerializer,
    FlowSerializer,
    FlowVersionSerializer,
    StepExecutionSerializer,
    StepSerializer,
)
from .sse import step_log_broker


@extend_schema_view(
    list=extend_schema(
        summary="Listar flujos de trabajo",
        description="Obtiene todos los flujos de trabajo (workflows) accesibles por el usuario. "
        "Los usuarios con permisos globales ven todos los flujos, mientras que los demás "
        "solo ven sus propios flujos.",
        tags=["Flows"],
    ),
    retrieve=extend_schema(
        summary="Obtener detalles de un flujo",
        description="Recupera la información completa de un flujo específico por su ID.",
        tags=["Flows"],
    ),
    create=extend_schema(
        summary="Crear un nuevo flujo",
        description="Crea un nuevo flujo de trabajo. Automáticamente inicializa una rama "
        "principal vacía para el flujo. El usuario autenticado se asigna como propietario.",
        tags=["Flows"],
    ),
    update=extend_schema(
        summary="Actualizar flujo completo",
        description="Actualiza todos los campos de un flujo existente (PUT completo).",
        tags=["Flows"],
    ),
    partial_update=extend_schema(
        summary="Actualizar flujo parcialmente",
        description="Actualiza campos específicos de un flujo existente (PATCH parcial).",
        tags=["Flows"],
    ),
    destroy=extend_schema(
        summary="Eliminar un flujo",
        description="Elimina permanentemente un flujo y todas sus versiones, ramas y "
        "nodos asociados.",
        tags=["Flows"],
    ),
)
class FlowViewSet(StandardEnvelopeMixin, viewsets.ModelViewSet):
    """ViewSet para gestión de flujos de trabajo (workflows)."""

    queryset = Flow.objects.all()
    serializer_class = FlowSerializer
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]
    permission_resource = "flows"
    permission_required = {
        "versions": ("flows", "read"),
        "create_version": ("flows", "write"),
    }

    def perform_create(self, serializer):
        flow = serializer.save(owner=self.request.user)
        # Inicializar rama principal automáticamente
        try:
            flow_services.initialize_main_branch(flow, self.request.user)
        except ValueError:
            # Si ya existe, ignorar (no debería pasar en creación)
            pass

    def get_permissions(self):  # type: ignore[override]
        """Permit 'mine' action to any authenticated user regardless of app ACL.

        Tests and API semantics expect the `/mine/` endpoint to be available to
        authenticated users to list their own flows even if they don't have
        broader HasAppPermission permissions. For other actions, fall back to
        the default permission logic (IsAuthenticated + HasAppPermission).
        """
        # action will be set by DRF for viewsets; as a fallback, also check
        # request path to be resilient in test environments where `action` may
        # not be set yet during permission resolution.
        if getattr(self, "action", None) == "mine":
            # Allow the view method to handle auth explicitly
            return [permissions.AllowAny()]
        req = getattr(self, "request", None)
        try:
            path = req.path if req is not None else ""
        except Exception:
            path = ""
        if path.endswith("/mine/"):
            return [permissions.AllowAny()]
        return super().get_permissions()

    @action(detail=False, methods=["post"], url_path="create-cadma1")
    @extend_schema(
        summary="Crear flujo CADMA 1 con paso inicial",
        description=(
            "Crea un flujo 'CADMA 1' con el primer paso 'crear familia de referencia'.\n"
            "Params del paso: { mode: 'existing'|'new', family_id?, name?, smiles_list? }"
        ),
        tags=["Flows"],
    )
    def create_cadma1(self, request):
        """Crea un flow con el primer paso 'create_reference_family' ejecutado."""
        user = request.user
        params = request.data or {}
        # Ejecutar el step lógicamente (agnóstico de flow) para producir outputs
        ctx = StepContext(user=user, data_stack=DataStack())
        result = execute_step("create_reference_family", ctx, params)

        # Crear Flow y primera versión + Step registro
        flow = Flow.objects.create(name="CADMA 1", description="", owner=user)
        flow_services.initialize_main_branch(flow, user)
        version = FlowVersion.objects.create(
            flow=flow, version_number=1, parent_version=None, created_by=user
        )
        step = Step.objects.create(
            flow_version=version,
            name="Crear familia de referencia",
            description="",
            step_type="create_reference_family",
            order=1,
            config={"params": params, "metadata": result.metadata},
        )

        ser = FlowSerializer(flow)
        return Response(
            {
                "flow": ser.data,
                "initial_step": step.id,
                "outputs": result.outputs,
            },
            status=status.HTTP_201_CREATED,
        )

    def get_queryset(self):  # type: ignore[override]
        """Soporta filtrado por propiedad del usuario y query param ?mine=true.

        - Si ?mine=true, devuelve solo flows del usuario.
        - En caso contrario, filtra según permisos (todas vs. propias).
        """
        qs = super().get_queryset()
        if self.request.query_params.get("mine") == "true":
            return qs.filter(owner=self.request.user)
        return flow_services.filter_flows_for_user(qs, self.request.user)

    @action(detail=True, methods=["get"])
    @extend_schema(
        summary="Listar versiones de un flujo",
        description="Obtiene todas las versiones (congeladas o no) de un flujo específico. "
        "Las versiones congeladas son instantáneas inmutables del flujo.",
        tags=["Flows"],
    )
    def versions(self, request, pk=None):
        """Obtiene todas las versiones de un flujo."""
        flow = self.get_object()
        versions = flow.versions.all()
        serializer = FlowVersionSerializer(versions, many=True)
        return Response(serializer.data)

    @action(
        detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated]
    )
    @extend_schema(
        summary="Listar mis flujos",
        description="Obtiene únicamente los flujos creados por el usuario autenticado, "
        "independientemente de los permisos globales que pueda tener.",
        tags=["Flows"],
    )
    def mine(self, request):
        """Devuelve los flows creados por el usuario autenticado.

        Note: we allow the permission check to be bypassed at the class level so
        we perform a simple authenticated check here to ensure only logged-in
        users can access their flows. This avoids dependence on HasAppPermission
        for the `/mine/` convenience endpoint used by frontends and tests.
        """
        if not request.user or not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        qs = self.get_queryset().filter(owner=request.user)
        serializer = FlowSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="create-branch")
    @extend_schema(
        summary="Crear rama en un flujo",
        description="Crea una nueva rama en el árbol del flujo a partir de un nodo específico "
        "de una rama existente. Permite experimentar con variaciones sin afectar otras ramas. "
        "No se permiten merges (arquitectura de árbol sin ciclos).",
        tags=["Flows", "Branches"],
    )
    def create_branch(self, request, pk=None):
        """Crea una nueva rama en el flujo."""
        flow = self.get_object()
        from .serializers import CreateBranchSerializer

        serializer = CreateBranchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            branch = flow_services.create_branch(
                serializer.validated_data["name"],
                flow,
                serializer.validated_data["from_branch"],
                serializer.validated_data["at_step"],
                request.user,
            )
            from .serializers import FlowBranchSerializer

            return Response(
                FlowBranchSerializer(branch).data, status=status.HTTP_201_CREATED
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def create_version(self, request, pk=None):
        """Create a new version for a flow"""
        flow = self.get_object()
        data = request.data.copy()
        data["flow"] = flow.id
        data["created_by"] = request.user.id

        serializer = FlowVersionSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"], url_path="definitions")
    def list_definitions_action(self, request):
        """List available flow definitions (predefined templates)."""
        return Response({"definitions": list_definitions()})

    @action(detail=False, methods=["post"], url_path="create-from-definition")
    def create_from_definition(self, request):
        """Create a flow instance from a registered definition.

        Body: { key: str, name?: str, params_override?: { index: dict } }
        """
        key = request.data.get("key")
        if not key:
            return Response(
                {"detail": "'key' is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        defn = get_definition(key)
        flow_name = request.data.get("name")
        raw_override = request.data.get("params_override") or {}
        # Coerce string indices to integers for builder compatibility
        params_override = {}
        if isinstance(raw_override, dict):
            for k, v in raw_override.items():
                try:
                    idx = int(k)
                except (TypeError, ValueError):
                    continue
                params_override[idx] = v
        flow = create_flow_from_definition(
            owner=request.user,
            defn=defn,
            name=flow_name,
            params_override=params_override,
        )
        ser = FlowSerializer(flow)
        return Response(ser.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    list=extend_schema(
        summary="Listar versiones de flujos",
        description="Obtiene todas las versiones de flujos del sistema que el usuario puede ver.",
        tags=["Flow Versions"],
    ),
    retrieve=extend_schema(
        summary="Obtener versión de flujo",
        description="Recupera los detalles de una versión específica de un flujo.",
        tags=["Flow Versions"],
    ),
    create=extend_schema(
        summary="Crear versión de flujo",
        description="Crea una nueva versión (snapshot) de un flujo. Las versiones pueden ser "
        "congeladas para hacerlas inmutables.",
        tags=["Flow Versions"],
    ),
    update=extend_schema(
        summary="Actualizar versión de flujo",
        description="Actualiza una versión de flujo (solo si no está congelada).",
        tags=["Flow Versions"],
    ),
    partial_update=extend_schema(
        summary="Actualizar versión parcialmente",
        description="Actualiza campos específicos de una versión (solo si no está congelada).",
        tags=["Flow Versions"],
    ),
    destroy=extend_schema(
        summary="Eliminar versión de flujo",
        description="Elimina una versión de flujo (típicamente no permitido si está congelada).",
        tags=["Flow Versions"],
    ),
)
class FlowVersionViewSet(StandardEnvelopeMixin, viewsets.ModelViewSet):
    """ViewSet para gestión de versiones de flujos (snapshots inmutables)."""

    queryset = FlowVersion.objects.all()
    serializer_class = FlowVersionSerializer
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]
    permission_resource = "flows"

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):  # type: ignore[override]
        qs = super().get_queryset()
        return flow_services.filter_versions_for_user(qs, self.request.user)

    @action(detail=True, methods=["post"])
    @extend_schema(
        summary="Congelar versión de flujo",
        description="Congela una versión de flujo, haciéndola inmutable. Una vez congelada, "
        "no puede ser modificada ni descongelada. Útil para preservar estados específicos.",
        tags=["Flow Versions"],
    )
    def freeze(self, request, pk=None):
        """Congela una versión de flujo (la hace inmutable)."""
        version = self.get_object()
        if version.is_frozen:
            return Response(
                {"error": "Version is already frozen"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        version.is_frozen = True
        version.save()
        serializer = self.get_serializer(version)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    @extend_schema(
        summary="Ejecutar versión de flujo",
        description="Crea un snapshot de ejecución para una versión de flujo. Registra inputs "
        "y metadata de la ejecución. Los resultados de cada paso se almacenan en step executions.",
        tags=["Executions"],
    )
    def execute(self, request, pk=None):
        """Ejecuta una versión de flujo creando un snapshot de ejecución."""
        version = self.get_object()
        inputs = request.data.get("inputs", {})

        snapshot = ExecutionSnapshot.objects.create(
            flow_version=version, triggered_by=request.user, metadata={"inputs": inputs}
        )

        serializer = ExecutionSnapshotSerializer(snapshot)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    list=extend_schema(
        summary="Listar pasos de flujos",
        description="Obtiene todos los pasos (tareas) definidos en los flujos del sistema.",
        tags=["Steps"],
    ),
    retrieve=extend_schema(
        summary="Obtener detalles de un paso",
        description="Recupera la información completa de un paso específico de un flujo.",
        tags=["Steps"],
    ),
    create=extend_schema(
        summary="Crear un paso",
        description="Crea un nuevo paso (tarea) en un flujo, definiendo su configuración, "
        "inputs esperados y outputs generados.",
        tags=["Steps"],
    ),
    update=extend_schema(
        summary="Actualizar paso completo",
        description="Actualiza todos los campos de un paso existente.",
        tags=["Steps"],
    ),
    partial_update=extend_schema(
        summary="Actualizar paso parcialmente",
        description="Actualiza campos específicos de un paso existente.",
        tags=["Steps"],
    ),
    destroy=extend_schema(
        summary="Eliminar un paso",
        description="Elimina un paso de un flujo.",
        tags=["Steps"],
    ),
)
class StepViewSet(StandardEnvelopeMixin, viewsets.ModelViewSet):
    """ViewSet para gestión de pasos (tareas) en flujos de trabajo."""

    queryset = Step.objects.all()
    serializer_class = StepSerializer
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]
    permission_resource = "flows"

    def get_queryset(self):  # type: ignore[override]
        qs = super().get_queryset()
        return flow_services.filter_steps_for_user(qs, self.request.user)

    @action(detail=False, methods=["get"], url_path="catalog")
    @extend_schema(
        summary="Catálogo de pasos disponibles",
        description="Lista los step types registrados con sus esquemas de entrada/salida",
        tags=["Steps"],
    )
    def catalog(self, request):
        return Response({"steps": list_step_specs()})

    @action(detail=True, methods=["post"], url_path="append-step")
    @extend_schema(
        summary="Agregar paso a la versión",
        description=(
            "Agrega un paso (por step_type) a la versión. Params del paso van en 'params'.\n"
            "Si faltan datos, se pueden inferir de un contexto anterior (simplificado)."
        ),
        tags=["Flow Versions", "Steps"],
    )
    def append_step(self, request, pk=None):
        version = self.get_object()
        payload = request.data or {}
        step_type = payload.get("step_type")
        params = payload.get("params") or {}
        order = (version.steps.aggregate(_max=models.Max("order")).get("_max") or 0) + 1
        if not step_type:
            return Response({"error": "step_type is required"}, status=400)

        # Ejecutar paso en un contexto nuevo (se podría rehidratar desde ejecución previa)
        ctx = StepContext(user=request.user, data_stack=DataStack())
        result = execute_step(step_type, ctx, params)

        step = Step.objects.create(
            flow_version=version,
            name=payload.get("name", step_type.replace("_", " ").title()),
            description=payload.get("description", ""),
            step_type=step_type,
            order=order,
            config={"params": params, "metadata": result.metadata},
        )
        return Response(StepSerializer(step).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="execute")
    @extend_schema(
        summary="Ejecutar step agnóstico",
        description=(
            "Ejecuta un step reutilizable sin pertenecer a un flujo.\n"
            "Body: { step_type: string, params: object }"
        ),
        tags=["Steps"],
    )
    def execute(self, request):
        payload = request.data or {}
        step_type = payload.get("step_type")
        params = payload.get("params") or {}
        if not step_type:
            return Response(
                {"error": "step_type is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        ctx = StepContext(user=request.user, data_stack=DataStack())
        result = execute_step(step_type, ctx, params)
        return Response(
            {"outputs": result.outputs, "metadata": result.metadata},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="run")
    @extend_schema(
        summary="Ejecutar un Step dentro de un snapshot",
        description=(
            "Ejecuta el Step seleccionado creando (o usando) un ExecutionSnapshot y "
            "registrando una StepExecution con logs SSE.\n"
            "Body opcional: { snapshot_id?: number, send_email?: boolean, webhook_url?: string }"
        ),
        tags=["Steps", "Executions"],
    )
    def run(self, request, pk=None):
        step = self.get_object()
        flow = step.flow_version.flow
        if not FlowPermissionService.can_user_execute_flow(request.user, flow):
            return Response(status=status.HTTP_403_FORBIDDEN)

        payload = request.data or {}
        snapshot_id = payload.get("snapshot_id")
        send_email = bool(payload.get("send_email", False))
        webhook_url = payload.get("webhook_url")
        override_params = payload.get("params")

        snapshot = None
        if snapshot_id:
            try:
                snapshot = ExecutionSnapshot.objects.get(
                    id=snapshot_id, flow_version=step.flow_version
                )
            except ExecutionSnapshot.DoesNotExist:
                return Response(
                    {"error": "snapshot_id inválido para este Step"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            snapshot = ExecutionSnapshot.objects.create(
                flow_version=step.flow_version,
                triggered_by=request.user,
                metadata={"inputs": step.config.get("params", {})},
            )

        # Iniciar ejecución
        step_exec = FlowExecutionService.start_step_execution(
            step, snapshot, send_email=send_email, webhook_url=webhook_url
        )
        # If runtime params are provided, store them in execution inputs
        if isinstance(override_params, dict):
            step_exec.inputs = override_params
            step_exec.save(update_fields=["inputs"])

        # Ejecutar lógica agnóstica del step
        try:
            FlowExecutionService.log_step_output(
                step_exec, f"Starting step '{step.step_type}'"
            )
            ctx = StepContext(user=request.user, data_stack=DataStack())
            effective_params = (
                override_params
                if isinstance(override_params, dict)
                else step.config.get("params", {})
            )
            result = execute_step(step.step_type, ctx, effective_params)
            # Persistir outputs del step
            step_exec.outputs = result.outputs or {}
            step_exec.save(update_fields=["outputs"])
            FlowExecutionService.complete_step_execution(
                step_exec, webhook_url=webhook_url
            )
            FlowExecutionService.complete_step_logs(step_exec)

            # Completar snapshot si no hay otras ejecuciones vinculadas
            other_exists = snapshot.step_executions.exclude(id=step_exec.id).exists()
            if not other_exists:
                FlowExecutionService.complete_flow_execution(
                    snapshot, webhook_url=webhook_url
                )

            return Response(
                StepExecutionSerializer(step_exec).data,
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:  # noqa: BLE001 - registramos el error textual
            FlowExecutionService.fail_step_execution(
                step_exec, str(e), webhook_url=webhook_url
            )
            FlowExecutionService.complete_step_logs(step_exec)
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema_view(
    list=extend_schema(
        summary="Listar artefactos",
        description="Obtiene todos los artefactos (archivos, datos) generados por flujos. "
        "Los artefactos son content-addressable (identificados por hash SHA256).",
        tags=["Artifacts"],
    ),
    retrieve=extend_schema(
        summary="Obtener detalles de artefacto",
        description="Recupera metadata de un artefacto específico, incluyendo hash, "
        "tipo de contenido y ubicación de almacenamiento.",
        tags=["Artifacts"],
    ),
    create=extend_schema(
        summary="Crear artefacto",
        description="Registra un nuevo artefacto en el sistema. El contenido debe ser "
        "almacenado en storage externo (S3/MinIO) y se registra el hash SHA256.",
        tags=["Artifacts"],
    ),
    update=extend_schema(
        summary="Actualizar artefacto completo",
        description="Actualiza metadata de un artefacto (no el contenido, que es inmutable).",
        tags=["Artifacts"],
    ),
    partial_update=extend_schema(
        summary="Actualizar artefacto parcialmente",
        description="Actualiza campos específicos de metadata de un artefacto.",
        tags=["Artifacts"],
    ),
    destroy=extend_schema(
        summary="Eliminar artefacto",
        description="Elimina el registro de un artefacto (no borra el contenido en storage).",
        tags=["Artifacts"],
    ),
)
class ArtifactViewSet(StandardEnvelopeMixin, viewsets.ModelViewSet):
    """ViewSet para gestión de artefactos content-addressable (archivos y datos)."""

    queryset = Artifact.objects.all()
    serializer_class = ArtifactSerializer
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]
    permission_resource = "flows"

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):  # type: ignore[override]
        qs = super().get_queryset()
        return flow_services.filter_artifacts_for_user(qs, self.request.user)

    @action(detail=True, methods=["get"])
    @extend_schema(
        summary="Obtener URL de descarga de artefacto",
        description="Genera o devuelve la URL de descarga para acceder al contenido del artefacto "
        "desde el almacenamiento externo (S3/MinIO). Actualmente retorna metadata.",
        tags=["Artifacts"],
    )
    def download(self, request, pk=None):
        """Obtiene la URL de descarga del archivo del artefacto."""
        artifact = self.get_object()
        return Response(
            {
                "download_url": f"/media/{artifact.storage_path}",
                "filename": artifact.filename,
            }
        )


@extend_schema_view(
    list=extend_schema(
        summary="Listar ejecuciones de flujos",
        description="Obtiene todos los snapshots de ejecución de flujos. Cada snapshot "
        "representa una ejecución completa de un flujo con sus inputs, outputs y metadata.",
        tags=["Executions"],
    ),
    retrieve=extend_schema(
        summary="Obtener detalles de ejecución",
        description="Recupera información completa de un snapshot de ejecución, incluyendo "
        "la versión del flujo ejecutada, usuario que la disparó y timestamp.",
        tags=["Executions"],
    ),
    create=extend_schema(
        summary="Crear snapshot de ejecución",
        description="Crea un nuevo snapshot de ejecución para un flujo. Típicamente se usa "
        "a través del endpoint execute de FlowVersion.",
        tags=["Executions"],
    ),
)
class ExecutionSnapshotViewSet(StandardEnvelopeMixin, viewsets.ModelViewSet):
    """ViewSet para gestión de snapshots de ejecución de flujos."""

    queryset = ExecutionSnapshot.objects.all()
    serializer_class = ExecutionSnapshotSerializer
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]
    permission_resource = "flows"

    def get_queryset(self):  # type: ignore[override]
        qs = super().get_queryset()
        return flow_services.filter_snapshots_for_user(qs, self.request.user)

    @action(detail=True, methods=["get"])
    @extend_schema(
        summary="Listar ejecuciones de pasos",
        description="Obtiene todas las ejecuciones de pasos individuales dentro de un snapshot "
        "de ejecución, incluyendo inputs, outputs, estado y artefactos generados.",
        tags=["Executions"],
    )
    def steps(self, request, pk=None):
        """Obtiene las ejecuciones de pasos de un snapshot."""
        snapshot = self.get_object()
        executions = snapshot.step_executions.all()
        serializer = StepExecutionSerializer(executions, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary="Listar todas las ejecuciones de pasos",
        description="Obtiene todas las ejecuciones individuales de pasos a través de todos "
        "los snapshots de ejecución.",
        tags=["Step Executions"],
    ),
    retrieve=extend_schema(
        summary="Obtener detalles de ejecución de paso",
        description="Recupera información detallada de la ejecución de un paso específico, "
        "incluyendo inputs, outputs, estado (success/failure), logs y artefactos producidos.",
        tags=["Step Executions"],
    ),
)
class StepExecutionViewSet(StandardEnvelopeMixin, viewsets.ModelViewSet):
    """ViewSet para gestión de ejecuciones individuales de pasos."""

    queryset = StepExecution.objects.all()
    serializer_class = StepExecutionSerializer
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]
    permission_resource = "flows"

    @action(detail=True, methods=["get"], url_path="status")
    @extend_schema(
        summary="Consultar estado de ejecución de un Step",
        description="Retorna el estado actual, timestamps y salida de la ejecución.",
        tags=["Step Executions"],
    )
    def status(self, request, pk=None):  # type: ignore[override]
        step_exec = self.get_object()
        flow = step_exec.step.flow_version.flow
        if not FlowPermissionService.can_user_read_flow(request.user, flow):
            return Response(status=status.HTTP_403_FORBIDDEN)
        data = {
            "id": step_exec.id,
            "status": step_exec.status,
            "started_at": step_exec.started_at,
            "completed_at": step_exec.completed_at,
            "error_message": step_exec.error_message,
            "outputs": step_exec.outputs,
        }
        return Response(data)

    @action(detail=True, methods=["post"], url_path="cancel")
    @extend_schema(
        summary="Cancelar ejecución de Step",
        description=(
            "Marca la ejecución como cancelada si está en estado pending/running y "
            "cierra el stream de logs."
        ),
        tags=["Step Executions"],
    )
    def cancel(self, request, pk=None):  # type: ignore[override]
        step_exec = self.get_object()
        flow = step_exec.step.flow_version.flow
        if not FlowPermissionService.can_user_execute_flow(request.user, flow):
            return Response(status=status.HTTP_403_FORBIDDEN)

        if step_exec.status in ("pending", "running"):
            step_exec.status = "cancelled"
            step_exec.completed_at = now()
            step_exec.save(update_fields=["status", "completed_at"])
            FlowExecutionService.log_step_output(
                step_exec, "Execution cancelled", event="cancel"
            )
            FlowExecutionService.complete_step_logs(step_exec)
            return Response({"ok": True})
        return Response(
            {"error": f"No se puede cancelar en estado {step_exec.status}"},
            status=status.HTTP_400_BAD_REQUEST,
        )


# ========================================================================
# SSE: Streaming de logs de StepExecution
# ========================================================================


@extend_schema(
    summary="Stream SSE de logs de un StepExecution",
    description=(
        "Devuelve un stream Server-Sent Events (text/event-stream) con los logs de "
        "ejecución de un step. Úsalo desde el frontend con EventSource."
    ),
    tags=["Executions", "SSE"],
    parameters=[
        OpenApiParameter(
            name="pk",
            description="ID del StepExecution",
            required=True,
            type=str,
            location=OpenApiParameter.PATH,
        )
    ],
)
def step_execution_logs_stream(request, pk: str):  # type: ignore[override]
    """Endpoint SSE para consumir logs en tiempo real de un StepExecution."""
    if not request.user or not request.user.is_authenticated:
        # Forzamos auth; si se requiere público, cambiar a AllowAny + tokens firmados
        raise Http404()

    try:
        step_execution = StepExecution.objects.select_related(
            "execution_snapshot__flow_version__flow__owner"
        ).get(pk=pk)
    except StepExecution.DoesNotExist:
        raise Http404()

    # Verificar permisos de lectura del flow
    flow = step_execution.step.flow_version.flow
    if not FlowPermissionService.can_user_read_flow(request.user, flow):
        raise Http404()

    def event_stream():
        # Comentario inicial para confirmar conexión
        yield ": connected\n\n"
        # Anunciar inicio
        step_log_broker.publish(
            step_execution.id,
            event="start",
            data={"at": now().isoformat()},
        )
        # Reenviar el stream del broker
        for chunk in step_log_broker.stream(step_execution.id):
            yield chunk

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    # Encabezados recomendados para SSE
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"  # Nginx: deshabilita buffering
    response["Connection"] = "keep-alive"
    return response


@extend_schema(
    summary="Append de log a un StepExecution",
    description=(
        "Publica una línea de log (o JSON) hacia los suscriptores del stream SSE del "
        "StepExecution. Acepta { line: string, event?: string, end?: boolean }."
    ),
    tags=["Executions", "SSE"],
)
def step_execution_logs_append(request, pk: str):  # type: ignore[override]
    """Endpoint para publicar logs a un StepExecution (solo usuarios autorizados)."""
    if request.method != "POST":
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    if not request.user or not request.user.is_authenticated:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    try:
        step_execution = StepExecution.objects.select_related(
            "execution_snapshot__flow_version__flow__owner", "step__flow"
        ).get(pk=pk)
    except StepExecution.DoesNotExist:
        raise Http404()

    # Verificar permiso de ejecución/escritura en el flujo
    flow = step_execution.step.flow_version.flow
    if not FlowPermissionService.can_user_execute_flow(request.user, flow):
        return Response(status=status.HTTP_403_FORBIDDEN)

    payload = request.data or {}
    line = payload.get("line", "")
    event_name = payload.get("event", "log")
    end_flag = bool(payload.get("end", False))

    if line:
        step_log_broker.publish(
            step_execution.id,
            event=event_name,
            data={"line": str(line), "at": now().isoformat()},
        )

    if end_flag:
        step_log_broker.complete(step_execution.id)

    return Response({"ok": True})


# ========================================================================
# ViewSets para árbol de nodos
# ========================================================================


@extend_schema_view(
    list=extend_schema(
        summary="Listar ramas de flujos",
        description="Obtiene todas las ramas en la estructura de árbol de flujos. Cada rama "
        "representa una línea de desarrollo independiente sin posibilidad de merge.",
        tags=["Branches"],
    ),
    retrieve=extend_schema(
        summary="Obtener detalles de una rama",
        description="Recupera información de una rama específica, incluyendo su nodo head "
        "(último paso) y nodo de inicio.",
        tags=["Branches"],
    ),
    create=extend_schema(
        summary="Crear nueva rama",
        description="Crea una rama bifurcando desde un nodo existente de otra rama. "
        "Implementa algoritmo de árbol sin merges ni ciclos.",
        tags=["Branches"],
    ),
    destroy=extend_schema(
        summary="Eliminar rama",
        description="Elimina una rama y todas sus sub-ramas recursivamente. Los nodos "
        "compartidos con otras ramas no se eliminan. No se puede eliminar la rama principal.",
        tags=["Branches"],
    ),
)
class FlowBranchViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de ramas en el árbol de flujos (sin merges)."""

    queryset = FlowBranch.objects.all()
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]
    permission_resource = "flows"

    def get_serializer_class(self):
        if self.action == "add_step":
            from .serializers import AddStepSerializer

            return AddStepSerializer
        elif self.action == "create":
            from .serializers import CreateBranchSerializer

            return CreateBranchSerializer
        else:
            from .serializers import FlowBranchSerializer

            return FlowBranchSerializer

    def get_queryset(self):  # type: ignore[override]
        qs = super().get_queryset()
        # Filtrar ramas de flows propios
        if not flow_services.user_can_read_all_flows(self.request.user):
            qs = qs.filter(flow__owner=self.request.user)
        return qs

    @action(detail=True, methods=["post"], url_path="add-step")
    @extend_schema(
        summary="Añadir paso a rama",
        description="Añade un nuevo nodo (paso) al final de una rama. Si el contenido "
        "(content hash) ya existe en el flujo, se reutiliza el nodo existente. "
        "Implementa deduplicación de nodos compartidos.",
        tags=["Branches"],
    )
    def add_step(self, request, pk=None):
        """Añade un paso a la rama."""
        branch = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            node = flow_services.add_step(
                branch.name,
                branch.flow,
                serializer.validated_data["content"],
                request.user,
            )
            from .serializers import FlowNodeSerializer

            return Response(
                FlowNodeSerializer(node).data, status=status.HTTP_201_CREATED
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"], url_path="path")
    @extend_schema(
        summary="Obtener camino completo de rama",
        description="Recupera la secuencia ordenada de nodos desde la raíz hasta el head "
        "de la rama. Útil para reconstruir el flujo lineal de una rama específica.",
        tags=["Branches"],
    )
    def path(self, request, pk=None):
        """Retorna el camino de nodos de la rama."""
        branch = self.get_object()
        try:
            path_nodes = flow_services.get_path(branch.name, branch.flow)
            from .serializers import FlowNodeSerializer

            return Response(FlowNodeSerializer(path_nodes, many=True).data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """DELETE /api/flows/branches/{id}/ - Elimina la rama y subramas recursivamente."""
        branch = self.get_object()
        if branch.name == "principal":
            return Response(
                {"error": "No se puede eliminar la rama principal"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            flow_services.delete_branch(branch.name, branch.flow)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        summary="Listar nodos de flujos",
        description="Obtiene todos los nodos (pasos) en el árbol de flujos. Los nodos "
        "pueden ser compartidos entre múltiples ramas (deduplicación por content_hash).",
        tags=["Nodes"],
    ),
    retrieve=extend_schema(
        summary="Obtener detalles de nodo",
        description="Recupera información de un nodo específico, incluyendo su contenido, "
        "padre y hash de contenido. Solo lectura.",
        tags=["Nodes"],
    ),
)
class FlowNodeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para nodos del árbol de flujos (solo lectura, deduplicación por hash)."""

    queryset = FlowNode.objects.all()
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]
    permission_resource = "flows"

    def get_serializer_class(self):
        from .serializers import FlowNodeSerializer

        return FlowNodeSerializer

    def get_queryset(self):  # type: ignore[override]
        qs = super().get_queryset()
        # Filtrar nodos de flows propios
        if not flow_services.user_can_read_all_flows(self.request.user):
            qs = qs.filter(flow__owner=self.request.user)
        return qs
