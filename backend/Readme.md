# ChemFlow Backend (Django + DRF)

Resumen

Backend modular con arquitectura hexagonal y principios SOLID. Dominios:

- Users: autenticación JWT, RBAC (roles/permissions), tokens
- Flows: workflows step-first, versiones, artefactos, árbol sin merges
- Chemistry: moléculas, propiedades (EAV), familias y relaciones
- Notifications: email/webhook/realtime con puertos/adaptadores

Arquitectura Hexagonal (Ports & Adapters)

- Dominio: entidades, value objects, reglas de negocio puras (sin framework)
- Aplicación: orquesta casos de uso, DTOs, servicios
- Infraestructura: Django ORM, DRF, email/webhooks/WebSocket mocks
- Interfaces: ViewSets/serializers HTTP como adaptadores

Principios SOLID aplicados

- SRP: cada clase hace una cosa (admin por modelo, servicio por caso de uso)
- OCP: servicios abiertos a extensión vía puertos (interfaces) y DI
- LSP: sustitución segura de adaptadores que implementan el mismo puerto
- ISP: interfaces pequeñas (IEmailSender, IWebhookSender, IRealtimeSender)
- DIP: dominio depende de puertos, adaptadores dependen de puertos

Bounded Contexts

- users/: User, Role, Permission, UserToken, auth JWT
- flows/: Flow, FlowVersion, Step, Artifact, Execution, árbol (FlowNode/Branch)
- chemistry/: Molecule, Family, propiedades (EAV)
- notifications/: domain, application, infrastructure

Estándares de código

- Tipado: mypy + django-stubs (mypy.ini configurado)
- Estilo: flake8 (max 100 chars), docstrings claras
- Serializers: validación explícita, read_only_fields definidos
- Permisos: permiso por recurso/acción (users.permissions.HasAppPermission)
- Servicios: lógica de negocio en services.py (no en views)
- Migraciones: determinísticas, sin side-effects salvo migraciones de datos con reversa

Ejecución local

1. Instalar dependencias (Python 3.12):

```bash
pip install -r backend/requirements.txt
```

1. Migraciones:

```bash
python backend/manage.py migrate
```

1. Crear datos de ejemplo (opcional):

```bash
python backend/manage.py seed_roles
python backend/manage.py seed_users
python backend/manage.py seed_molecules
python backend/manage.py seed_flows
```

1. Ejecutar servidor:

```bash
python backend/manage.py runserver
```

1. Tests:

```bash
pytest -q
```

Puntos de extensión

- Notificaciones: reemplace mocks por adaptadores reales (SMTP, Channels)
- Artefactos: cambie storage_path a almacenamiento S3/GCS mediante repositorio
- Árbol de flujos: políticas de validación y control de concurrencia

Convenciones de permisos

Resource:Action

- users: read/write/delete
- flows: read/write/execute/delete
- chemistry: read/write/delete

Checklist de calidad

- Build: Django check/migrate PASS
- Lint: flake8 sin errores de estilo críticos
- Types: mypy sin errores en módulos de dominio/aplicación
- Tests: unitarios mínimos por bounded context
