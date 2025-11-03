# ChemFlow Backend - Documentación

## 📋 Descripción General

ChemFlow Backend es una API REST construida con **Django 5.2** y **Django REST Framework** que gestiona flujos de trabajo (workflows) complejos en el dominio químico. La arquitectura sigue principios de **Domain-Driven Design (DDD)** con capas claramente separadas: Domain, Application, Infrastructure e Interfaces.

**Características principales:**

- ✅ Gestión de flujos de trabajo con versionado y ramificación sin merge
- ✅ Dominio químico con moléculas, familias y propiedades (ADMETSA)
- ✅ Ejecución de pasos con tracking de artifacts
- ✅ Autenticación JWT y control de acceso
- ✅ Notificaciones en tiempo real (WebSocket, Email, Webhooks)
- ✅ API OpenAPI/Swagger documentada

---

## 🏗️ Arquitectura del Proyecto

### Capas Arquitectónicas (Hexagonal)

```
┌─────────────────────────────────────────────────────────┐
│                    INTERFACES                            │
│  (REST Views, Serializers, OpenAPI)                      │
└─────────────────────────────────────────────────────────┘
                         ↕
┌─────────────────────────────────────────────────────────┐
│              APPLICATION LAYER                           │
│  (Services, Use Cases, DTOs, Ports)                      │
└─────────────────────────────────────────────────────────┘
                         ↕
┌─────────────────────────────────────────────────────────┐
│                 DOMAIN LAYER                             │
│  (Entities, Value Objects, Business Logic)              │
└─────────────────────────────────────────────────────────┘
                         ↕
┌─────────────────────────────────────────────────────────┐
│            INFRASTRUCTURE LAYER                          │
│  (Adapters, Database, External Services)                │
└─────────────────────────────────────────────────────────┘
```

### Estructura de Directorios

```
backend/
├── back/                          # Configuración principal
│   ├── settings.py               # Configuración Django
│   ├── urls.py                   # Rutas principales
│   ├── wsgi.py                   # WSGI para producción
│   ├── asgi.py                   # ASGI para WebSocket
│   └── routing.py                # Rutas WebSocket
├── chemistry/                    # App: Dominio químico
│   ├── models.py                 # Modelos ORM
│   ├── views.py                  # ViewSets REST
│   ├── serializers.py            # Serializadores
│   ├── services.py               # Servicios de dominio
│   ├── urls.py                   # Rutas
│   ├── providers/                # Motores de cálculo (RDKit)
│   └── management/commands/      # Comandos CLI
├── flows/                        # App: Flujos de trabajo
│   ├── models.py                 # Modelos de Flow, Step, etc
│   ├── views.py                  # ViewSets REST
│   ├── serializers.py            # Serializadores
│   ├── services.py               # Servicios
│   ├── consumers.py              # WebSocket consumers
│   ├── domain/                   # Capa de dominio
│   │   └── flujo/               # Lógica de flujos
│   ├── application/              # Capa de aplicación
│   │   ├── services.py
│   │   └── ports.py
│   ├── infrastructure/           # Capa de infraestructura
│   │   └── chemistry_adapter.py
│   └── management/commands/
├── notifications/                # App: Notificaciones
│   ├── models.py
│   ├── views.py
│   ├── domain/                   # Entidades y eventos
│   ├── application/              # Use cases
│   └── infrastructure/           # Adaptadores
├── users/                        # App: Usuarios
│   ├── models.py                 # Modelo User personalizado
│   ├── views.py
│   └── serializers.py
└── manage.py                     # Script de Django
```

---

## 📊 Diagrama de Base de Datos

```sql
-- DOMINIO QUÍMICO
┌──────────────────┐
│   users_user     │
├──────────────────┤
│ id (PK)          │
│ username         │
│ email            │
│ password_hash    │
│ is_active        │
│ created_at       │
└──────────────────┘
         │
         │ created_by (FK)
         ↓
┌──────────────────────────────┐         ┌─────────────────┐
│    chemistry_molecule        │         │  chemistry_     │
├──────────────────────────────┤         │   family        │
│ id (PK)                      │◄───────→├─────────────────┤
│ inchikey (UNIQUE)            │ members │ id (PK)         │
│ smiles                       │         │ name            │
│ inchi                        │         │ family_hash     │
│ canonical_smiles             │         │ provenance      │
│ molecular_formula            │         │ frozen          │
│ created_by (FK → users_user) │         │ created_at      │
│ created_at                   │         └─────────────────┘
│ frozen                       │                  │
│ metadata (JSON)              │                  │ families_properties
└──────────────────────────────┘                  ↓
         │                         ┌──────────────────────────┐
         │ properties              │ chemistry_family_        │
         ↓                         │ property                 │
┌──────────────────────────────┐  ├──────────────────────────┤
│  chemistry_molecular_        │  │ id (PK)                  │
│  property                    │  │ family_id (FK)           │
├──────────────────────────────┤  │ property_type            │
│ id (PK)                      │  │ value                    │
│ molecule_id (FK)             │  │ method                   │
│ property_type                │  │ units                    │
│ value                        │  │ source_id                │
│ method                       │  │ is_invariant             │
│ units                        │  │ created_at               │
│ source_id                    │  └──────────────────────────┘
│ is_invariant                 │
│ created_at                   │  ┌──────────────────────────┐
└──────────────────────────────┘  │ chemistry_family_        │
                                  │ member                   │
                                  ├──────────────────────────┤
                                  │ id (PK)                  │
                                  │ family_id (FK)           │
                                  │ molecule_id (FK)         │
                                  └──────────────────────────┘

-- FLUJOS DE TRABAJO
┌────────────────────────┐
│      flows_flow        │
├────────────────────────┤
│ id (PK)                │
│ owner_id (FK→users)    │
│ name                   │
│ description            │
│ created_at             │
│ updated_at             │
└────────────────────────┘
         │
         │ versions
         ↓
┌────────────────────────────────┐
│    flows_flow_version          │
├────────────────────────────────┤
│ id (PK)                        │
│ flow_id (FK)                   │
│ version_number                 │
│ parent_version_id (FK self)    │
│ is_frozen                      │
│ created_at                     │
│ created_by_id (FK→users)       │
└────────────────────────────────┘
         │
         │ steps
         ↓
┌────────────────────────────────┐
│       flows_step               │
├────────────────────────────────┤
│ id (PK)                        │
│ flow_version_id (FK)           │
│ name                           │
│ step_type                      │
│ order                          │
│ config (JSON)                  │
│ created_at                     │
└────────────────────────────────┘
         │
         ├─→ dependencies
         │   ┌──────────────────────────┐
         │   │ flows_step_dependency    │
         │   ├──────────────────────────┤
         │   │ id (PK)                  │
         │   │ step_id (FK)             │
         │   │ depends_on_step_id (FK)  │
         │   └──────────────────────────┘
         │
         └─→ executions
             ┌──────────────────────────┐
             │  flows_execution_        │
             │  snapshot                │
             ├──────────────────────────┤
             │ id (PK)                  │
             │ flow_id (FK)             │
             │ status                   │
             │ started_at               │
             │ completed_at             │
             │ metadata (JSON)          │
             └──────────────────────────┘
                      │
                      │ step_executions
                      ↓
             ┌──────────────────────────┐
             │  flows_step_execution    │
             ├──────────────────────────┤
             │ id (PK)                  │
             │ execution_id (FK)        │
             │ step_id (FK)             │
             │ status                   │
             │ started_at               │
             │ completed_at             │
             │ result (JSON)            │
             └──────────────────────────┘
                      │
                      └─→ artifacts
                          ┌──────────────────────────┐
                          │ flows_artifact           │
                          ├──────────────────────────┤
                          │ id (PK)                  │
                          │ content_hash (UNIQUE)    │
                          │ content (JSONField)      │
                          │ created_at               │
                          └──────────────────────────┘
```

---

## ⚙️ AMBIT-SA (Java) – Configuración rápida

Algunos ejemplos y el proveedor de Accesibilidad Sintética (SA) basados en **AMBIT-SA** requieren una JRE 8 y el JAR `SyntheticAccessibilityCli.jar`.

Opciones de configuración:

- Vía variables de entorno o archivo `.env` en `backend/`:
  - `AMBIT_JAVA_PATH`: ruta al binario de Java (ej. `.../jre8/bin/java`)
  - `AMBIT_JAR_PATH`: ruta al JAR `SyntheticAccessibilityCli.jar`

Valores por defecto (si no defines variables):

- `AMBIT_JAVA_PATH = backend/tools/java/jre8/bin/java`
- `AMBIT_JAR_PATH = backend/tools/external/ambitSA/SyntheticAccessibilityCli.jar`

Descarga automática (Linux):

- Descarga JRE 8 portable (local a este repo)
  - Ejecuta: `scripts/download_java_runtimes.sh` → instala en `tools/java/jre8/`
- Descarga herramientas externas (incluye AMBIT-SA)
  - Ejecuta: `scripts/download_external_tools.sh` → instala en `tools/external/ambitSA/`

Luego puedes verificar AMBIT con los ejemplos:

- `python backend/examples/test_ambit.py`
- `python backend/examples/rdkit_sa_example.py`
- `python backend/examples/brsascore_example.py`

Si el JAR o Java no están disponibles, verás un error claro indicando qué ruta falta. Ajusta las variables en `.env` o coloca los binarios en las rutas por defecto indicadas arriba.

---

## 🔄 Diagrama de Flujo de Datos

### 1️⃣ Creación de un Flujo (CADMA)

```
┌─────────────────────┐
│   Usuario Browser   │
└──────────┬──────────┘
           │
           │ POST /api/flows/
           │ { name, definition_key: "cadma" }
           ↓
┌──────────────────────────┐
│  FlowViewSet.create()    │
│  (views.py)              │
└──────────┬───────────────┘
           │
           │ Delega a FlowApplicationService
           ↓
┌──────────────────────────────────────────┐
│ FlowApplicationService.create_flow()     │
│ (application/services.py)                │
└──────────┬───────────────────────────────┘
           │
           │ Obtiene definición: get_definition("cadma")
           ↓
┌──────────────────────────────────────────┐
│ FlowDefinition (predefined_cadma.py)     │
│ [Step1: CreateRefFamily,                 │
│  Step2: GenerateADMETSA,                 │
│  Step3: CreateRefMoleculeFamily,         │
│  Step4: GenerateSubstitutionFamily,      │
│  Step5: GenerateADMETSAFamilyAgg]        │
└──────────┬───────────────────────────────┘
           │
           │ Ejecuta builder
           ↓
┌──────────────────────────────────────────┐
│ create_flow_from_definition()            │
│ (domain/flujo/builder.py)                │
│                                          │
│ @transaction.atomic:                     │
│  1. Crea Flow                            │
│  2. Crea FlowVersion v1                  │
│  3. Por cada step en definición:         │
│     - Crea Step object                   │
│     - Crea StepDependency                │
└──────────┬───────────────────────────────┘
           │
           ↓
┌──────────────────────────────────────────┐
│ Django ORM Persist                       │
│ (INSERT into flows_flow,                 │
│  flows_flow_version, flows_step, etc.)   │
└──────────┬───────────────────────────────┘
           │
           ↓
┌──────────────────────────────────────────┐
│ Response 201                             │
│ { id, name, current_version, steps }     │
└──────────────────────────────────────────┘
```

### 2️⃣ Ejecución de un Paso (Step Execution)

```
┌──────────────────────┐
│ Usuario/Sistema      │
└──────────┬───────────┘
           │
           │ POST /api/flows/{id}/execute/
           │ { step_id, params: {...} }
           ↓
┌──────────────────────────────────────────┐
│ FlowViewSet.execute() (views.py)         │
└──────────┬───────────────────────────────┘
           │
           │ 1. Valida permisos
           │ 2. Obtiene Step config
           │ 3. Construye StepContext
           ↓
┌──────────────────────────────────────────┐
│ StepContext (interface.py)               │
│ - user: User                             │
│ - params: Dict[str, Any]                 │
│ - data_stack: DataStack                  │
│ - step_spec: StepSpec                    │
└──────────┬───────────────────────────────┘
           │
           │ Busca handler del step type
           │ (step registry)
           ↓
┌──────────────────────────────────────────┐
│ StepHandler (ej: CreateRefFamily)        │
│ (domain/steps/create_reference_family.py)│
│                                          │
│ async def execute(context):              │
│   # Llama services de Chemistry          │
│   # Procesa entrada, valida              │
│   # Genera outputs                       │
│   # Retorna StepResult                   │
└──────────┬───────────────────────────────┘
           │
           │ Interactúa con Chemistry
           ↓
┌──────────────────────────────────────────┐
│ chemistry.services (ports)               │
│ - create_family_from_smiles()            │
│ - get_admetsa_properties()               │
│ - etc.                                   │
└──────────┬───────────────────────────────┘
           │
           │ Retorna datos
           ↓
┌──────────────────────────────────────────┐
│ StepResult                               │
│ { outputs: Dict, metadata: Dict }        │
└──────────┬───────────────────────────────┘
           │
           │ Persiste ejecución
           ↓
┌──────────────────────────────────────────┐
│ StepExecution.save() + Artifacts         │
│ (modelos en flows/models.py)             │
└──────────┬───────────────────────────────┘
           │
           │ Emit WebSocket evento
           ↓
┌──────────────────────────────────────────┐
│ FlowCollaborationConsumer.send_json()    │
│ (consumers.py)                           │
│ broadcast: { event, step_id, result }    │
└──────────────────────────────────────────┘
```

---

## 📦 Modelos Principales

### Clase: `Molecule`

Representa una entidad molecular con invariantes químicos.

```python
class Molecule:
    id: int
    inchikey: str           # Identificador único
    smiles: str             # SMILES notation
    inchi: str              # InChI format
    canonical_smiles: str
    molecular_formula: str
    created_by: User        # Foreign Key
    properties: List[MolecularProperty]
```

**Relaciones:**

- `1:N` → MolecularProperty (propiedades EAV)
- `N:M` → Family (mediante FamilyMember)
- `N:M` → Flow (mediante MoleculeFlow)

---

### Clase: `Flow`

Representa un flujo de trabajo con versionado.

```python
class Flow:
    id: int
    owner: User             # Foreign Key
    name: str
    versions: List[FlowVersion]
    created_at: datetime
    updated_at: datetime
```

**Relaciones:**

- `1:N` → FlowVersion
- `1:N` → Step (indirecto vía FlowVersion)
- `1:N` → ExecutionSnapshot

---

### Clase: `Step`

Representa un paso individual en un flujo.

```python
class Step:
    id: int
    flow_version: FlowVersion   # FK
    name: str
    step_type: str              # "chemistry.admetsa", etc
    order: int
    config: Dict[str, Any]      # Configuración específica
    dependencies: List[Step]    # Via StepDependency
```

**Relaciones:**

- `N:1` → FlowVersion
- `N:N` → Step (autoreferencial vía StepDependency)

---

## 🚀 Puntos de Entrada API

### Chemistry API

```
GET    /api/chemistry/molecules/               # Listar moléculas
POST   /api/chemistry/molecules/               # Crear molécula
GET    /api/chemistry/molecules/{id}/          # Detalle
PATCH  /api/chemistry/molecules/{id}/          # Actualizar
DELETE /api/chemistry/molecules/{id}/          # Eliminar

GET    /api/chemistry/families/                # Listar familias
POST   /api/chemistry/families/create_from_smiles/  # Crear desde SMILES
GET    /api/chemistry/families/{id}/           # Detalle
```

### Flows API

```
GET    /api/flows/                            # Listar flujos
POST   /api/flows/                            # Crear flujo
GET    /api/flows/{id}/                       # Detalle
POST   /api/flows/{id}/execute/               # Ejecutar paso
GET    /api/flows/{id}/versions/              # Versiones
POST   /api/flows/{id}/branch/                # Crear rama

GET    /api/flows/{flow_id}/steps/            # Pasos
GET    /api/flows/{flow_id}/executions/       # Ejecuciones
GET    /api/flows/step-executions/{id}/logs/stream/  # SSE logs
```

### Users & Auth

```
POST   /api/auth/token/                       # Obtener JWT
POST   /api/auth/token/refresh/               # Refrescar token
GET    /api/users/me/                         # Usuario actual
GET    /api/users/                            # Listar usuarios (admin)
```

---

## 🔐 Autenticación & Autorización

### Flujo JWT

1. Usuario envía `username` + `password` → POST `/api/auth/token/`
2. Backend valida y retorna `access_token` + `refresh_token`
3. Cliente incluye `Authorization: Bearer {access_token}` en requests
4. Backend valida firma JWT
5. Si expira → POST `/api/auth/token/refresh/` con `refresh_token`

### Permisos

- **IsAuthenticated**: Requiere JWT válido
- **IsOwner**: Usuario debe ser propietario del recurso
- **Admin**: Usuario con flag `is_staff=True`

---

## 🔄 WebSocket (Colaboración Real-Time)

### Ruta

```
ws://localhost:8000/ws/flows/{flow_id}/
```

### Eventos

#### Cliente → Server

```json
{
  "type": "node_change",
  "payload": {
    "node_id": 123,
    "position": { "x": 100, "y": 200 }
  }
}
```

#### Server → Cliente (Broadcast)

```json
{
  "type": "node_changed",
  "user_id": 5,
  "username": "alice",
  "payload": {...}
}
```

---

## 📝 Servicios Principales

### `chemistry.services`

Lógica de negocio para el dominio químico.

- `create_family_from_smiles()` - Crea familia desde SMILES
- `get_admetsa_properties()` - Calcula propiedades ADMETSA
- `filter_molecules_for_user()` - Control de acceso

### `flows.application.services`

Orquestación de flujos.

- `FlowApplicationService.create_flow()` - Crea flow desde definición
- `FlowApplicationService.execute_step()` - Ejecuta paso

### `flows.domain.steps.interface`

Registro y ejecución de pasos.

- `execute_step()` - Ejecuta un paso con contexto
- `register_step()` - Registra handler de paso

---

## ⚙️ Configuración

### Variables de Entorno (.env)

```bash
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
CHEM_ENGINE=rdkit              # Motor químico
DATABASE_URL=sqlite:///db.sqlite3
EMAIL_BACKEND=console          # Desarrollo
FRONTEND_URL=http://localhost:4200
```

### Settings

- `INSTALLED_APPS`: Django apps (users, flows, chemistry, notifications)
- `REST_FRAMEWORK`: Autenticación JWT, permisos
- `SPECTACULAR_SETTINGS`: OpenAPI/Swagger
- `CORS_ALLOWED_ORIGINS`: Para frontend local

---

## 🧪 Testing

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Con cobertura
pytest --cov=.

# Solo una app
pytest flows/tests/
```

### Estructura

```
app_name/
├── tests.py                 # Tests de app
├── tests/
│   ├── test_models.py
│   ├── test_views.py
│   ├── test_services.py
│   └── fixtures/
```

---

## 📚 Comandos Útiles

### Setup Inicial

```bash
cd backend
python manage.py migrate              # Ejecutar migraciones
python manage.py seed_molecules      # Poblar datos de ejemplo
python manage.py reset_flows --seed-cadma  # Reset + crear flow CADMA
```

### Desarrollo

```bash
python manage.py runserver            # Servidor local
python manage.py makemigrations       # Crear migraciones
python manage.py shell                # Shell de Django
```

### Admin

```bash
python manage.py createsuperuser      # Crear superusuario
# Acceder a http://localhost:8000/admin/
```

### Validación

```bash
mypy .                                # Type checking
pytest --cov                          # Tests con cobertura
```

---

## 🎯 Patrones de Diseño

### 1. Domain-Driven Design

- **Domain Layer**: Entidades y lógica core
- **Application Layer**: Use cases y orquestación
- **Infrastructure Layer**: Adaptadores y persistencia
- **Interfaces Layer**: REST API

### 2. Ports & Adapters (Hexagonal)

```
IChemistryPort (Interface)
    ↑
    └── ChemistryAdapter (Implementación)
        └── chemistry.services (Adaptado)
```

### 3. Data Stack Pattern

Acumula datos producidos por steps para referencias posteriores:

```python
data_stack = {
    "chemistry.family": {...},
    "chemistry.admetsa_set": {...}
}
```

### 4. Step Registry

Registro de handlers de pasos ejecutables.

---

## 📖 Referencias

- [Django Docs](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [SimpleJWT](https://django-rest-framework-simplejwt.readthedocs.io/)
- [drf-spectacular](https://drf-spectacular.readthedocs.io/)
- [RDKit](https://www.rdkit.org/)

---

## 🤝 Contribución

1. Crear rama: `git checkout -b feature/nombre`
2. Cambios + tests
3. Validar: `mypy .` + `pytest`
4. Commit: `git commit -am 'feat: descripción'`
5. Push + PR

---

## 📄 Licencia

MIT License - Ver [LICENSE](../LICENSE) para más detalles.

Este proyecto está bajo la licencia MIT, la cual es altamente permisiva y permite:

- ✅ Uso comercial
- ✅ Modificación
- ✅ Distribución
- ✅ Uso privado
- ⚠️ Con la única condición de incluir la licencia y copyright
