# Guía de Reconstrucción: ChemFlow (Arquitectura Step-First)

## Resumen y objetivos

Este documento define cómo reconstruir ChemFlow adoptando una arquitectura step-first, con contratos API primero (OpenAPI 3.1), monorepo Angular + Django, y un modelo de datos que permite congelar estados (snapshots), versionar artefactos, y manejar ramas de flujos sin merges (árbol). El orden de las tablas es: Usuarios y permisos → Sistema de flujos → Química.

## Arquitectura y tecnologías

- Frontend: Angular 18+, Angular Material, señales (signals), formularios dinámicos (Formly), validación con Zod, SSR opcional (Angular Universal).
- Backend: Django 5+, Django REST Framework (DRF) con drf-spectacular (OpenAPI), autenticación JWT (SimpleJWT), PostgreSQL.
- Contratos: Diseño API-first con OpenAPI 3.1; generación de clientes en Angular a partir del contrato.
- Persistencia: PostgreSQL (JSONB para metadatos); artefactos content-addressable (sha256) en almacenamiento tipo S3/MinIO.
- Orquestación: Step-first con snapshots inmutables, ejecución registrando entradas/salidas por paso y artefactos producidos.

## Estructura de carpetas (monorepo sugerida)

Vista de alto nivel para un monorepo Angular + Django, contratos y herramientas de desarrollo.

```text
chem-flow/
├─ frontend/                         # App Angular (Editor de flujos + Paneles)
│  ├─ package.json                   # Dependencias y scripts de frontend
│  ├─ angular.json                   # Configuración Angular
│  └─ src/
│     ├─ index.html
│     ├─ styles.scss
│     └─ app/
│        ├─ app.ts / app.routes.ts / app.config.ts
│        ├─ core/                   # Núcleo: guards, interceptors, state
│        │  ├─ guards/
│        │  ├─ interceptors/
│        │  └─ state/
│        ├─ models/                 # Tipos TS: flows, chemistry, users
│        ├─ services/               # Servicios: API, editor state, SSE
│        ├─ components/             # Board, node card, toolbar, panels
│        ├─ pages/                  # Dashboard, editor, login
│        ├─ shared/                 # UI reutilizable (dialogs, utils)
│        └─ assets/                 # Íconos, imágenes
│
├─ backend/                          # API Django + DRF + OpenAPI
│  ├─ manage.py
│  ├─ pyproject.toml | requirements.txt
│  ├─ chemflow/                     # Proyecto Django
│  │  ├─ settings.py
│  │  ├─ urls.py
│  │  ├─ asgi.py
│  │  └─ wsgi.py
│  └─ apps/
│     ├─ users/                     # Usuarios, roles, permisos, ACL
│     │  ├─ models.py
│     │  ├─ serializers.py
│     │  ├─ views.py
│     │  ├─ urls.py
│     │  ├─ permissions.py
│     │  ├─ tests/
│     │  └─ migrations/
│     ├─ flows/                     # Flujos, snapshots, runs, artifacts, ramas
│     │  ├─ models.py
│     │  ├─ serializers.py
│     │  ├─ views.py
│     │  ├─ urls.py
│     │  ├─ services.py (orquestación)
│     │  ├─ sse.py (eventos SSE)
│     │  ├─ tests/
│     │  └─ migrations/
│     └─ chemistry/                 # Moléculas, familias y propiedades (minimal)
│        ├─ models.py
│        ├─ serializers.py
│        ├─ views.py
│        ├─ urls.py
│        ├─ tests/
│        └─ migrations/
│
├─ contracts/                        # OpenAPI y esquemas compartidos
│  └─ openapi.yaml
│
├─ infra/                            # Infra de desarrollo y despliegue
│  ├─ docker-compose.dev.yml
│  └─ env/
│     ├─ backend.env
│     └─ frontend.env
│
├─ scripts/                          # Utilidades (codegen, migraciones de datos)
│  ├─ codegen-client.sh
│  └─ seed-dev-data.py
│
├─ docs/                             # Documentación adicional
│  └─ design-spec.md
│
├─ .github/workflows/                # CI/CD
│  └─ ci.yml
│
├─ REBUILD_GUIDE.md                  # Esta guía
└─ README.md
```

Notas:

- En proyectos que ya tienen un frontend en raíz (como el actual), la migración a monorepo puede hacerse moviendo el contenido a `frontend/` y creando `backend/` en paralelo.
- Para storybook o documentación viva de componentes, añadir `frontend/.storybook/` (opcional).
- Para caching de CI, configurar rutas de `node_modules` y `.venv`/`.cache/pip` según el gestor usado.

## ¿Cómo funciona ChemFlow (de punta a punta)?

Objetivo: generar y mantener información química de familias de moléculas y de moléculas individuales mediante flujos de trabajo versionados.

### Flujo operativo

#### Autoría del flujo en el editor visual

- El usuario arma un grafo de pasos (nodos) y conexiones con el editor visual.
- Cada paso define sus entradas y salidas (por ejemplo: SMILES de moléculas, configuraciones de cálculo, criterios de agregación).
- Se valida en tiempo real con Zod/Formly y reglas del editor (sin ciclos, sin merges, ramas bien formadas).

#### Congelado del flujo (snapshot)

- Al guardar, se genera un snapshot inmutable con hash de contenido (content_hash) y versión.
- El snapshot contiene el grafo y la configuración exacta de cada paso.

#### Ejecución

- Se crea un run referenciando el snapshot. Opcionalmente se pasan overrides de parámetros.
- La orquestación recorre pasos en orden topológico por ramas. Para cada paso lee entradas (propiedades previas, moléculas/familias seleccionadas, artefactos), ejecuta la lógica declarada (cálculo, enriquecimiento, filtrado, exportación) y registra eventos.

#### Persistencia de resultados

- Propiedades moleculares: se escriben en molecular_properties con property_type, value, units, method, relation, source_id (id del run/step) y metadata.
- Propiedades de familia: se escriben en family_properties con la misma estructura. Las propiedades agregadas (promedios, medianas, conteos) se calculan a partir de los miembros (family_members) o de resultados de pasos.
- Artefactos (tablas/CSV/imágenes): se almacenan en flow_artifacts como objetos direccionables por hash (sha256) con media_type.

#### Consulta y trazabilidad

- Cualquier propiedad tiene trazabilidad vía source_id (run/step), method (experimental/calculated) y metadata (condiciones, parámetros).
- La inmutabilidad del snapshot garantiza reproducibilidad: volver a ejecutar un snapshot produce el mismo pipeline; si cambias el flujo, generas un nuevo snapshot.

Notas de versión y actualización:

- En el esquema minimalista, las filas de propiedades pueden actualizarse (no son append-only). Si se requiere historial, guarda versiones en metadata o conserva el valor previo y referencia el run/step anterior.

Casos de uso típicos:

- Familias: seleccionar una familia, generar propiedades agregadas (p. ej., promedio de logP), validar criterios (Lipinski), exportar resultados.
- Moléculas individuales: calcular ADMET, predecir solubilidad, asignar etiquetas; luego agregar a familias y recalcular agregados.

## Editor visual de flujos (Frontend)

Componentes clave:

Servicios y estado:

- BoardStateService: nodos, conexiones, selección, undo/redo.
- BoardLayoutService: posicionamiento y rutas de conexión.
- BoardInteractionService: drag & drop, selección, atajos de teclado (setas, Enter, Delete), enfoque accesible.
- FlowEditorStateService (sugerido): orquestación de UI, persistencia del estado del editor y sincronización con backend.

Accesibilidad y UX:

- Elementos con roles ARIA adecuados (button, group), foco visible, navegación por teclado.
- Contraste suficiente y tamaños táctiles.
- Virtualización a partir de >50 nodos y lazy-loading de detalles.

Dependencias recomendadas (Angular):

- @angular/material, @angular/cdk
- @ngx-formly/core y @ngx-formly/material (formularios dinámicos)
- zod (validación) y zod-to-json-schema (opcional para interoperar con Formly)
- rxjs
- Opcional: SmilesDrawer o rdkit-js para render de moléculas en el cliente (si no se usa imagen precalculada)

## Formularios de pasos (Frontend)

Estrategia:

- Cada tipo de paso declara un esquema de entrada/salida (StepContract) validado con Zod.
- Los formularios se generan con Formly a partir de un JSON (o de un schema traducido desde Zod), manteniendo consistencia y reuso.
- Validaciones síncronas (Zod) y reglas del editor (por ejemplo, puertos compatibles) antes de permitir guardar/ejecutar.

Patrón (contrato mínimo del paso):

- inputs: claves y tipos esperados (ej. family_id, molecule_inchikey[], thresholds).
- outputs: qué persiste (ej. property_type/value en tablas de propiedades, artifacts con sha256).
- errores: shape estándar con códigos y mensajes user-friendly.

Ejemplos de pasos:

- Seleccionar familia: input family_id; output set de molecule_inchikey de la familia.
- Generar ADMET: input molecule_inchikey[] + parámetros; output molecular_properties (p. ej., logP, solubility) y artifacts (CSV).
- Agregación de familia: input family_id + property_type; output family_properties (promedio/mediana/rango) con units y method="calculated".

## Orquestación y APIs (Backend)

Endpoints mínimos (DRF):

- Flujos:
  - GET/POST /api/flows
  - GET/POST /api/flows/{id}/snapshots
  - POST /api/runs — body: { snapshot_id, params? }
  - GET /api/runs/{id}
  - GET /api/runs/{id}/events — SSE de eventos del run
- Química:
  - GET/POST /api/molecules
  - GET/POST /api/families
  - GET/POST /api/molecular-properties
  - GET/POST /api/family-properties

Ejecución (sin ejecutor externo):

- Un servicio de orquestación en Django recorre el grafo del snapshot (orden topológico por ramas) y ejecuta cada paso como función Python pura.
- Para cada paso, persiste resultados en tablas y emite eventos (yield) a un endpoint SSE.
- Tareas largas: se puede iniciar en background thread/process controlado por el propio backend (mínimo), o integrar más adelante un broker (opcional) si escala.

Eventos en tiempo real (SSE):

- Implementar un StreamingHttpResponse que emite líneas "data: {json}\n\n" por evento.
- Frontend se conecta con EventSource y actualiza el panel de eventos.

Dependencias recomendadas (Django):

- djangorestframework, drf-spectacular, djangorestframework-simplejwt
- django-filter, django-cors-headers
- psycopg2-binary (PostgreSQL)
- django-storages + boto3 (para S3/MinIO de artifacts) — opcional
- rdkit (en entorno de cálculo, si se hacen cómputos químicos en backend) — opcional

## Frontend (Angular) – Especificaciones y paquetería

- Angular 18+, angular.json con builder moderno, rutas standalone y signals.
- UI: @angular/material, theming con SCSS.
- Formularios: @ngx-formly/core, @ngx-formly/material.
- Validación: zod y adaptador para validar schemas de entradas/salidas de pasos.
- Utilidades: rxjs; opcional dayjs/date-fns.
- Pruebas: Jest o runner nativo de Angular 18 (elige uno y estandariza en CI).
- Lint: ESLint.

Sugerencia de dependencias (frontend):

- @angular/core, @angular/router, @angular/material
- @ngx-formly/core, @ngx-formly/material
- zod
- rxjs

## Backend (Django) – Especificaciones y paquetería

- Django 5+
- djangorestframework
- drf-spectacular (OpenAPI 3.1)
- djangorestframework-simplejwt (JWT)
- django-filter, django-cors-headers
- psycopg2-binary (PostgreSQL)

## Contratos (OpenAPI 3.1)

- Diseño contracts-first: definir paths, schemas (flows, snapshots, runs, artifacts, moléculas, familias y propiedades), y seguridad (JWT Bearer) en openapi.yaml.
- Generar el cliente Angular desde el contrato.

Ejemplo mínimo de paths para flujos:

```yaml
openapi: 3.1.0
info: { title: ChemFlow API, version: 0.1.0 }
paths:
  /api/flows:
    get: { summary: Listar flujos }
    post: { summary: Crear flujo }
  /api/flows/{id}/snapshots:
    get: { summary: Listar snapshots }
    post: { summary: Crear snapshot }
  /api/runs:
    post: { summary: Ejecutar snapshot }
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

## Modelo de datos: Usuarios y permisos

```sql
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  username TEXT UNIQUE NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS roles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT UNIQUE NOT NULL,
  description TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_roles (
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
  PRIMARY KEY (user_id, role_id)
);

CREATE TABLE IF NOT EXISTS permissions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT UNIQUE NOT NULL,
  description TEXT
);

CREATE TABLE IF NOT EXISTS role_permissions (
  role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
  permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
  PRIMARY KEY (role_id, permission_id)
);

-- ACL por recurso (recurso puede ser flow/snapshot/artifact, sujeto user o role)
CREATE TABLE IF NOT EXISTS acl_entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  resource_type TEXT NOT NULL,
  resource_id TEXT NOT NULL,
  subject_type TEXT NOT NULL, -- 'user' | 'role'
  subject_id TEXT NOT NULL,
  action TEXT NOT NULL,       -- 'read' | 'write' | 'execute' | 'admin'
  effect TEXT NOT NULL DEFAULT 'allow', -- 'allow' | 'deny'
  UNIQUE (resource_type, resource_id, subject_type, subject_id, action)
);
```

## Modelo de datos: Sistema de flujos

```sql
CREATE TABLE IF NOT EXISTS flows (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  description TEXT,
  owner_id UUID REFERENCES users(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  archived BOOLEAN NOT NULL DEFAULT FALSE,
  metadata JSONB
);

CREATE TABLE IF NOT EXISTS flow_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  flow_id UUID NOT NULL REFERENCES flows(id) ON DELETE CASCADE,
  version INTEGER NOT NULL,
  content JSONB NOT NULL,    -- Grafo/DSL serializado
  content_hash TEXT NOT NULL, -- sha256 del contenido
  created_by UUID REFERENCES users(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  frozen BOOLEAN NOT NULL DEFAULT TRUE,
  UNIQUE (flow_id, version),
  UNIQUE (content_hash)
);

CREATE TABLE IF NOT EXISTS flow_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  flow_snapshot_id UUID NOT NULL REFERENCES flow_snapshots(id) ON DELETE RESTRICT,
  status TEXT NOT NULL, -- 'queued','running','succeeded','failed','canceled'
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  triggered_by UUID REFERENCES users(id) ON DELETE SET NULL,
  metadata JSONB
);

CREATE TABLE IF NOT EXISTS flow_artifacts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sha256 TEXT NOT NULL UNIQUE,
  media_type TEXT NOT NULL,
  size_bytes BIGINT NOT NULL,
  storage_url TEXT NOT NULL, -- s3://bucket/key o file://...
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata JSONB
);

CREATE TABLE IF NOT EXISTS flow_run_artifacts (
  run_id UUID NOT NULL REFERENCES flow_runs(id) ON DELETE CASCADE,
  step_id TEXT NOT NULL, -- id lógico del paso dentro del snapshot
  artifact_id UUID NOT NULL REFERENCES flow_artifacts(id) ON DELETE CASCADE,
  role TEXT NOT NULL, -- 'input' | 'output' | 'log'
  PRIMARY KEY (run_id, step_id, artifact_id, role)
);

-- Modelo de ramas (árbol): nodos y aristas por snapshot; ramas nombradas por flujo
CREATE TABLE IF NOT EXISTS flow_nodes (
  id TEXT NOT NULL,
  flow_snapshot_id UUID NOT NULL REFERENCES flow_snapshots(id) ON DELETE CASCADE,
  type TEXT NOT NULL,
  spec JSONB NOT NULL,
  position JSONB,
  PRIMARY KEY (flow_snapshot_id, id)
);

CREATE TABLE IF NOT EXISTS flow_node_children (
  flow_snapshot_id UUID NOT NULL,
  parent_id TEXT NOT NULL,
  child_id TEXT NOT NULL,
  edge_spec JSONB,
  PRIMARY KEY (flow_snapshot_id, parent_id, child_id),
  FOREIGN KEY (flow_snapshot_id, parent_id) REFERENCES flow_nodes(flow_snapshot_id, id) ON DELETE CASCADE,
  FOREIGN KEY (flow_snapshot_id, child_id) REFERENCES flow_nodes(flow_snapshot_id, id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS flow_branches (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  flow_id UUID NOT NULL REFERENCES flows(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  base_snapshot_id UUID REFERENCES flow_snapshots(id),
  head_snapshot_id UUID REFERENCES flow_snapshots(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (flow_id, name)
);
```

## Química (Esquema Simplificado)

```sql
-- Tabla para moléculas: Almacena estructuras únicas con identificadores invariantes. Se eliminó 'atom_count' ya que es derivable de SMILES/InChI; se agregó 'canonical_smiles' para estandarización como en ChEMBL.
CREATE TABLE IF NOT EXISTS molecules (
  inchikey TEXT PRIMARY KEY,  -- Clave primaria única basada en InChIKey para unicidad molecular.
  smiles TEXT NOT NULL,       -- Representación SMILES de la molécula.
  inchi TEXT NOT NULL,        -- Representación InChI completa.
  canonical_smiles TEXT,      -- SMILES canónico invariante, agregado para consistencia estructural.
  molecular_formula TEXT,     -- Fórmula molecular derivada, invariante.
  metadata JSONB,             -- Metadatos en JSON, e.g., {"source": "PubChem", "created_by": "workflow1"} para condiciones y procedencia.
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- Timestamp para inmutabilidad y auditoría.
  frozen BOOLEAN NOT NULL DEFAULT FALSE  -- Bandera para congelar actualizaciones, asegurando inmutabilidad.
);

-- Tabla para familias: Agrupa moléculas relacionadas. Se mantuvo 'family_hash' para integridad, pero se simplificó eliminando campos redundantes.
CREATE TABLE IF NOT EXISTS families (
  id TEXT PRIMARY KEY,        -- Identificador único de la familia.
  name TEXT,                  -- Nombre descriptivo de la familia.
  description TEXT,           -- Descripción detallada.
  family_hash TEXT NOT NULL,  -- Hash para verificación de integridad.
  provenance TEXT NOT NULL,   -- Procedencia o origen de la familia.
  frozen BOOLEAN NOT NULL DEFAULT TRUE,  -- Congelado por defecto para inmutabilidad en agregados.
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- Timestamp para rastreo.
  metadata JSONB              -- Metadatos en JSON, e.g., {"avg_method": "calculated"} para propiedades familiares específicas.
);

-- Tabla para propiedades de familias: Maneja propiedades agregadas como promedios. Se eliminó 'quality' y 'preferred'; se agregaron 'units' y 'relation' para estandarización como en ChEMBL; 'source_id' para trazabilidad.
CREATE TABLE IF NOT EXISTS family_properties (
  id TEXT PRIMARY KEY,        -- Identificador único de la propiedad.
  family_id TEXT NOT NULL REFERENCES families(id) ON DELETE CASCADE,  -- Referencia a familia.
  property_type TEXT NOT NULL, -- Tipo de propiedad, e.g., 'average_mass', 'pH'.
  value TEXT NOT NULL,        -- Valor de la propiedad (texto general para flexibilidad).
  value_hash TEXT NOT NULL,   -- Hash del valor para verificación (mantenido para inmutabilidad).
  is_invariant BOOLEAN NOT NULL DEFAULT FALSE,  -- Bandera para propiedades absolutas vs. variables.
  method TEXT,                -- Método: 'experimental', 'calculated', etc.
  units TEXT,                 -- Unidades estandarizadas, e.g., 'g/mol', agregado para precisión.
  relation TEXT,              -- Relación, e.g., '=', '>', agregado para contexto como en ChEMBL.
  source_id TEXT,             -- ID de fuente, agregado para metadatos de procedencia.
  metadata JSONB,             -- Metadatos en JSON, e.g., {"conditions": "25°C"}.
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- Timestamp para versiones.
  UNIQUE (family_id, property_type, method)  -- Constraint para evitar duplicados por contexto.
);

-- Tabla para propiedades moleculares: Similar a family_properties. Eliminaciones y adiciones iguales para consistencia.
CREATE TABLE IF NOT EXISTS molecular_properties (
  id TEXT PRIMARY KEY,        -- Identificador único.
  molecule_inchikey TEXT NOT NULL REFERENCES molecules(inchikey) ON DELETE CASCADE,  -- Referencia a molécula.
  property_type TEXT NOT NULL, -- Tipo, e.g., 'pH'.
  value TEXT NOT NULL,        -- Valor.
  value_hash TEXT NOT NULL,   -- Hash para integridad.
  is_invariant BOOLEAN NOT NULL DEFAULT FALSE,  -- Invariante vs. variable.
  method TEXT,                -- Método de obtención.
  units TEXT,                 -- Unidades, agregado.
  relation TEXT,              -- Relación, agregado.
  source_id TEXT,             -- Fuente, agregado.
  metadata JSONB,             -- Metadatos contextuales.
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (molecule_inchikey, property_type, method)
);

-- Tabla para miembros de familias: Relaciones muchos-a-muchos. Se simplificó eliminando redundancias.
CREATE TABLE IF NOT EXISTS family_members (
  id TEXT PRIMARY KEY,        -- Identificador único.
  family_id TEXT NOT NULL REFERENCES families(id) ON DELETE CASCADE,  -- Referencia a familia.
  molecule_inchikey TEXT NOT NULL REFERENCES molecules(inchikey) ON DELETE CASCADE,  -- Referencia a molécula.
  UNIQUE (family_id, molecule_inchikey)  -- Evita duplicados en membresías.
);
```

Consejos de Implementación

- Bases Relacionales (p. ej., PostgreSQL): usar triggers para hacer cumplir inmutabilidad en campos frozen. Para flujos variables, insertar nuevas propiedades en lugar de actualizar.
- No Relacionales (p. ej., MongoDB): embebido de propiedades como arrays para consultas rápidas en workflows heterogéneos.
- Estándares: alineado con ChEMBL para propiedades variables y PubChem para unicidad molecular. Usar RDKit para derivar invariantes.

En el diseño de bases de datos químicas, es fundamental equilibrar la rigidez estructural para mantener la integridad de los datos con la flexibilidad para manejar propiedades diversas y workflows variados. Este esquema refinado se basa en estándares establecidos como ChEMBL y PubChem, eliminando elementos innecesarios (p. ej., campos subjetivos como 'quality', 'preferred') que no aportan valor en contextos estandarizados, y agregando campos esenciales como 'units' y 'relation' para manejar propiedades variables con precisión. Además, se incorpora 'source_id' para mejorar la trazabilidad y metadatos, alineado con principios FAIR (Findable, Accessible, Interoperable, Reusable) que enfatizan la reproducibilidad científica.

Comparación con Estándares:

- En bases relacionales, se prioriza la normalización para reducir redundancias, usando claves foráneas y constraints robustos (inspirado en el uso de molregno en ChEMBL).
- PubChem distingue 'Substances' (datos depositados, variables) y 'Compounds' (estandarizados, invariantes), inspirando separar propiedades invariantes (p. ej., fórmulas derivadas) en molecules; las variables (p. ej., pH dependiente de método) se gestionan en tablas EAV con metadatos contextuales.

Manejo de Inmutabilidad y Metadatos:

- La inmutabilidad se logra con 'frozen' (bloquea updates) y 'created_at' (versionado append-only). Metadatos en JSONB permiten condiciones experimentales sin rigidizar el esquema.

## Flujo de trabajo

1. `docker compose up`.
2. Migrate: `docker exec backend python manage.py migrate`.
3. Develop: Access frontend at localhost:4200, backend at 8000.

## Migración de legado

1. Auditoría: Identifica módulos heredados que deban archivarse o refactorizarse y registra un reporte.
2. Refactor/Archivo: Mueve el código heredado a `legacy/` y refactoriza a StepContract donde corresponda.
3. Adaptadores: Crea adaptadores de conversión si es necesario.
4. Pruebas: Asegura no introducir regresiones con pruebas E2E.

## Plan de implementación (cronograma realista)

Fase 1: Scaffold (1 semana)

- Generar OpenAPI YAML (usar Swagger Editor).
- Configurar monorepo: inicializar proyectos Angular/Django.
- Implementar modelos/migraciones en Django.
- Generar cliente de API en Angular.
- Crear un FlowEditor básico.
- Configurar Docker Compose.

Fase 2: Funcionalidades núcleo (2 semanas)

- Implementar el modelo de ramas (BD + API).
- Añadir autenticación/permisos.
- Endpoints del catálogo de química.
- Lógica de snapshots/ejecuciones.

Fase 3: Pulido frontend (1 semana)

- Formularios dinámicos con Formly.
- Estado del editor con signals.
- Componentes UI (tema Material).

Fase 4: Pruebas y pulido (1 semana)

- Añadir pruebas.
- Migrar legado.
- Optimizar (índices, caché).

Total: 5 semanas (escala según tamaño del equipo).

## Próximas acciones

1. Generar scaffold: di "Sí, generar scaffold" para crear archivos (openapi.yaml, models.py, etc.).
2. Auditoría de legado: di "Listar legado" para obtener el reporte.
3. StepContract TS: di "Implementar StepContract TS" para tipos Zod/servicio.

Esta arquitectura es modular y lista para implementar, priorizando estándares sin perder practicidad. Si necesitas ajustes, indícalos.
