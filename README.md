# ChemFlow - Flujos de Trabajo Químicos

**Sistema completo de gestión de flujos de trabajo para análisis molecular, predicción ADMETSA y experimentación química.**

```
╔═══════════════════════════════════════════════════════════════════════╗
║                        CHEMFLOW ARCHITECTURE                         ║
║                                                                       ║
║  ┌────────────────────────────────────────────────────────────────┐  ║
║  │               ANGULAR 20 FRONTEND (Standalone)                │  ║
║  │  Dashboard | Flows | Chemistry | Canvas | Executions | Logs   │  ║
║  └────────────────────┬─────────────────────────────────────────┘  ║
║                       │ REST API + WebSocket                       ║
║  ┌────────────────────┴─────────────────────────────────────────┐  ║
║  │             DJANGO 5.2 REST BACKEND (Hexagonal)             │  ║
║  │                                                               │  ║
║  │  ┌──────────────────┬──────────────────┬──────────────────┐  │  ║
║  │  │ FLOWS APP        │ CHEMISTRY APP    │ NOTIFICATIONS    │  │  ║
║  │  │ (Workflows)      │ (Molecules)      │ (Real-time)      │  │  ║
║  │  └──────────────────┴──────────────────┴──────────────────┘  │  ║
║  │                                                               │  ║
║  │  Domain | Application | Infrastructure | Interfaces         │  ║
║  └────────────────────┬─────────────────────────────────────────┘  ║
║                       │                                             ║
║  ┌────────────────────┴─────────────────────────────────────────┐  ║
║  │         SQLITE3 / PostgreSQL (Development/Production)       │  ║
║  │                                                               │  ║
║  │  Users | Flows | Steps | Chemistry | Notifications          │  ║
║  └────────────────────────────────────────────────────────────────┘  ║
║                                                                       ║
║  🚀 Technology Stack:                                               ║
║  • Backend: Django 5.2, DRF, SimpleJWT, Channels, RDKit            ║
║  • Frontend: Angular 20, RxJS, SCSS, Signals                       ║
║  • Database: SQLite (dev), PostgreSQL (production)                 ║
║  • Real-time: WebSocket (Django Channels)                          ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

## 📚 Documentación Rápida

- 📖 **[Backend README](./backend/README.md)** - Arquitectura Django, modelos, APIs, diagramas BD
- 📖 **[Frontend README](./frontend/README.md)** - Arquitectura Angular, componentes, servicios, diseño
- 🔧 **[Este archivo]** - Setup y ejecución del proyecto completo

---

## ⚡ Quick Start (5 minutos)

### Requisitos Previos

```bash
# Backend
python 3.10+
pip
sqlite3 (incluido)

# Frontend
node 18.x o superior
npm 9.x o superior

# Opcional
postgresql 12+ (para producción)
redis 6+ (para caché)
```

### 1️⃣ Clonar y Navegar

```bash
# Ya estás aquí, pero:
cd /home/cesar/Documents/Proyectos/flow
ls -la
# flow/
# ├── backend/
# ├── frontend/
# └── README.md (este archivo)
```

### 2️⃣ Backend - Setup

```bash
cd backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o: venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Variables de entorno (opcional, usa valores por defecto)
cat > .env << EOF
DJANGO_SECRET_KEY=dev-secret-key-not-for-production
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
CHEM_ENGINE=rdkit
DATABASE_URL=sqlite:///db.sqlite3
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
FRONTEND_URL=http://localhost:4200
EOF

# Migrar base de datos
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser
# Username: admin
# Email: admin@example.com
# Password: (tu contraseña)

# Cargar datos de ejemplo (OPCIONAL)
python manage.py seed_molecules
python manage.py reset_flows --seed-cadma

# Iniciar servidor
python manage.py runserver
# http://127.0.0.1:8000
```

**✅ Backend está listo en:** `http://127.0.0.1:8000`

**API Endpoints:**

- API REST: `http://127.0.0.1:8000/api/`
- Admin: `http://127.0.0.1:8000/admin/`
- Swagger: `http://127.0.0.1:8000/api/docs/swagger/`
- ReDoc: `http://127.0.0.1:8000/api/docs/redoc/`

---

### 3️⃣ Frontend - Setup

```bash
# En otra terminal
cd frontend

# Instalar dependencias
npm install

# Variables de entorno (opcional)
cat > src/app/config.ts << EOF
export const BACKEND_URL = 'http://127.0.0.1:8000';
export const API_PREFIX = \`\${BACKEND_URL}\`;
EOF

# Iniciar servidor de desarrollo
npm start
# http://localhost:4200 (se abre automáticamente)
```

**✅ Frontend está listo en:** `http://localhost:4200`

---

## 🔑 Credenciales de Prueba

Después de crear el superusuario, usa estas credenciales:

```
Usuario: admin
Contraseña: (la que estableciste)
```

O crea un usuario de prueba:

```bash
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> User.objects.create_user('testuser', 'test@example.com', 'password123')
>>> exit()
```

Luego en la UI:

1. Ir a `http://localhost:4200/login`
2. Usuario: `testuser`
3. Contraseña: `password123`

---

## 📋 Flujo Típico de Uso

### 1. Crear un Flujo CADMA

```
1. Dashboard → Nuevo Flujo
2. Seleccionar "CADMA" en definiciones predefinidas
3. Nombrar flujo (ej: "CADMA - Molécula Test")
4. Crear → Flujo creado con 5 pasos predefinidos
```

### 2. Ejecutar un Paso

```
1. Flujo Detail → Tab "Steps"
2. Seleccionar paso "Create Reference Family"
3. Input:
   - Mode: "new"
   - Name: "Mi Familia"
   - SMILES: ["CCO", "CC(C)O", "CCCO"]
4. Ejecutar → Logs en streaming
5. Output: family_id, family_name
```

### 3. Ver Resultados

```
1. Tab "Executions" → Lista de ejecuciones
2. Seleccionar una ejecución
3. Ver pasos ejecutados y artifacts generados
4. Expandir un step → Ver entrada/salida/metadata
```

### 4. Colaboración en Tiempo Real

```
1. Abrir flujo en 2 navegadores (mismo usuario)
2. En uno: modificar nodo posición en canvas
3. En otro: ver cambio automático (WebSocket)
```

---

## 🛠️ Desarrollo Local

### Estructura del Proyecto

```
flow/
├── backend/                          # Django REST API
│   ├── manage.py
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── back/                         # Configuración Django
│   ├── chemistry/                    # App: Moléculas
│   ├── flows/                        # App: Flujos
│   ├── notifications/                # App: Notificaciones
│   ├── users/                        # App: Usuarios
│   └── README.md                     # Documentación backend
│
├── frontend/                         # Angular App
│   ├── package.json
│   ├── angular.json
│   ├── tsconfig.json
│   ├── src/
│   │   ├── app/
│   │   │   ├── pages/               # Vistas
│   │   │   ├── shared/              # Componentes reutilizables
│   │   │   ├── services/            # Servicios HTTP/WS
│   │   │   └── app.routes.ts        # Rutas
│   │   └── main.ts
│   └── README.md                     # Documentación frontend
│
└── README.md                         # Este archivo
```

### Comandos Útiles

#### Backend

```bash
cd backend

# Servicio
python manage.py runserver              # Iniciar (puerto 8000)
python manage.py runserver 0.0.0.0:8000 # Accesible desde red

# Migraciones
python manage.py makemigrations [app]   # Crear migraciones
python manage.py migrate                # Aplicar migraciones
python manage.py showmigrations         # Ver estado

# Shell interactivo
python manage.py shell

# Testing
pytest                                  # Todos los tests
pytest flows/tests/                     # Tests de una app
pytest --cov=.                          # Con cobertura
pytest -v                               # Verbose

# Admin
python manage.py createsuperuser        # Crear admin
python manage.py changepassword user    # Cambiar contraseña

# Datos
python manage.py seed_molecules         # Cargar moléculas
python manage.py seed_flows             # Cargar flujos
python manage.py reset_flows            # Limpiar flujos
python manage.py recompute_admetsa      # Recalcular propiedades
```

#### Frontend

```bash
cd frontend

# Desarrollo
npm start                               # Iniciar (puerto 4200)
npm run build                           # Build producción
npm test                                # Tests
ng lint                                 # Linting

# Generación
npm run generate:api                    # Generar API desde OpenAPI

# Instalación de paquetes
npm install package-name
npm install --save-dev @types/package-name
```

---

## 🔌 API Endpoints Principales

### Autenticación

```
POST /api/auth/token/
  • Body: { username, password }
  • Return: { access, refresh }

POST /api/auth/token/refresh/
  • Body: { refresh }
  • Return: { access }
```

### Flows

```
GET    /api/flows/                          # Listar (paginado)
POST   /api/flows/                          # Crear
GET    /api/flows/{id}/                     # Detalle
POST   /api/flows/{id}/execute/             # Ejecutar paso
GET    /api/flows/{id}/versions/            # Versiones
POST   /api/flows/{id}/branch/              # Crear rama

GET    /api/flows/step-executions/{id}/logs/stream/  # SSE logs
```

### Chemistry

```
GET    /api/chemistry/molecules/            # Listar
POST   /api/chemistry/molecules/            # Crear
GET    /api/chemistry/molecules/{id}/       # Detalle

GET    /api/chemistry/families/             # Listar
POST   /api/chemistry/families/create_from_smiles/  # Crear
GET    /api/chemistry/families/{id}/        # Detalle
```

### Users

```
GET    /api/users/me/                       # Usuario actual
GET    /api/users/                          # Listar (admin)
POST   /api/users/                          # Crear (admin)
GET    /api/users/{id}/                     # Detalle
```

---

## 🗄️ Base de Datos

### Esquema Principal

```sql
-- Usuarios
users_user
├── id (PK)
├── username (UNIQUE)
├── email
├── password_hash
├── is_active
├── is_staff
└── created_at

-- Flujos
flows_flow
├── id (PK)
├── owner_id (FK → users)
├── name
├── description
└── created_at

flows_flow_version
├── id (PK)
├── flow_id (FK)
├── version_number
├── parent_version_id (FK self)
└── is_frozen

flows_step
├── id (PK)
├── flow_version_id (FK)
├── name
├── step_type
├── order
└── config (JSON)

flows_step_dependency
├── id (PK)
├── step_id (FK)
└── depends_on_step_id (FK)

flows_execution_snapshot
├── id (PK)
├── flow_id (FK)
├── status
├── started_at
└── completed_at

flows_step_execution
├── id (PK)
├── execution_id (FK)
├── step_id (FK)
├── status
├── result (JSON)
└── completed_at

-- Chemistry
chemistry_molecule
├── id (PK)
├── inchikey (UNIQUE)
├── smiles
├── inchi
├── canonical_smiles
├── molecular_formula
├── created_by_id (FK → users)
└── created_at

chemistry_family
├── id (PK)
├── name
├── family_hash
├── provenance
└── frozen

chemistry_molecular_property
├── id (PK)
├── molecule_id (FK)
├── property_type
├── value
├── method
├── units
└── created_at

chemistry_family_member
├── id (PK)
├── family_id (FK)
├── molecule_id (FK)
└── UNIQUE(family_id, molecule_id)
```

### Consultas Útiles SQLite

```bash
cd backend

# Abrir shell SQLite
sqlite3 db.sqlite3

# Ver tablas
.tables

# Contar registros
SELECT COUNT(*) FROM chemistry_molecule;
SELECT COUNT(*) FROM flows_flow;

# Ver usuarios
SELECT id, username, email FROM users_user;

# Ver flujos de un usuario
SELECT f.id, f.name FROM flows_flow f WHERE f.owner_id = 1;

# Ver pasos de un flujo
SELECT s.id, s.name, s.step_type FROM flows_step s
JOIN flows_flow_version fv ON s.flow_version_id = fv.id
WHERE fv.flow_id = 1;

# Salir
.quit
```

---

## 📊 Monitoreo & Debugging

### Logs Backend

```bash
# Terminal con servidor
# Los logs aparecen automáticamente:
[14/Oct/2025 10:30:00] "POST /api/flows/" 201 Created
[14/Oct/2025 10:30:01] "GET /api/flows/1/" 200 OK

# Aumentar verbosidad
# En settings.py:
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
```

### Logs Frontend

```typescript
// En consola del navegador (F12)
console.log("Mi mensaje");
console.error("Error:", err);

// Ver requests HTTP
// DevTools → Network tab → Ver requests a http://127.0.0.1:8000/api/
```

### Django Admin

```
http://127.0.0.1:8000/admin/
• Usuario: admin
• Contraseña: (la que creaste)
```

Aquí puedes:

- Ver usuarios, flujos, pasos, moléculas
- Editar registros
- Ver relaciones
- Filtrar y buscar

---

## 🐛 Troubleshooting

### Backend no inicia

```bash
# Error: ModuleNotFoundError: No module named 'django'
pip install -r requirements.txt

# Error: No database tables
python manage.py migrate

# Error: Secret key issues
Editar settings.py y usar valor por defecto
```

### Frontend no inicia

```bash
# Error: Cannot find module '@angular/core'
npm install

# Error: ng command not found
npm install -g @angular/cli

# Error: Port 4200 already in use
ng serve --port 4201
```

### No puedo conectar backend desde frontend

```bash
# Verificar CORS en backend/back/settings.py:
CORS_ALLOWED_ORIGINS = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
]

# Verificar config en frontend/src/app/config.ts:
export const BACKEND_URL = 'http://127.0.0.1:8000';
```

### WebSocket no conecta

```bash
# Verificar que backend tiene Django Channels configurado
# En settings.py: INSTALLED_APPS incluye 'channels'
# En asgi.py: ProtocolTypeRouter configurado

# En consola del navegador:
# Debería conectarse a: ws://127.0.0.1:8000/ws/flows/1/
```

---

## 🚀 Deployment (Producción)

### Backend

```bash
# Usar servidor ASGI con Daphne o Uvicorn
pip install daphne

# O Gunicorn + Uvicorn
pip install gunicorn uvicorn

# Variables de entorno (.env o variables del sistema)
DJANGO_SECRET_KEY=tu-secret-key-largo-y-aleatorio
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=tudominio.com
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

### Frontend

```bash
# Build
npm run build

# Salida en dist/
# Servir con nginx o Apache

# nginx.conf
server {
    listen 80;
    server_name tudominio.com;
    root /var/www/chemflow/dist;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000/api/;
    }
}
```

---

## 📚 Documentación Completa

Consulta los README específicos para detalles técnicos profundos:

### Backend

📖 [backend/README.md](./backend/README.md)

- Arquitectura hexagonal detallada
- Diagramas de BD y clases
- Servicios y puertos
- Testing
- Configuración avanzada

### Frontend

📖 [frontend/README.md](./frontend/README.md)

- Arquitectura de componentes
- Diseño system tokens
- Servicios HTTP/WebSocket
- Patrones Angular (signals, computed, effects)
- Testing con Jasmine/Karma

---

## 👥 Equipo de Desarrollo

- **Arquitecto**: [Tu nombre]
- **Backend**: Django, DRF, Channels, RDKit
- **Frontend**: Angular, RxJS, SCSS
- **DevOps**: Docker, PostgreSQL, Nginx

---

## 📞 Soporte

Para problemas o preguntas:

1. Consulta la documentación en cada carpeta (backend/README.md, frontend/README.md)
2. Revisa los comentarios en el código
3. Ejecuta tests: `pytest` (backend), `npm test` (frontend)
4. Abre un issue en el repositorio

---

## 📄 Licencia

MIT License - Ver [LICENSE](./LICENSE) para más detalles.

Este proyecto está bajo la licencia MIT, la cual es altamente permisiva y permite:

- ✅ Uso comercial
- ✅ Modificación
- ✅ Distribución
- ✅ Uso privado
- ⚠️ Con la única condición de incluir la licencia y copyright

---

Después del setup básico, puedes:

1. **Explorar el Admin**: http://127.0.0.1:8000/admin/
2. **Ver API Docs**: http://127.0.0.1:8000/api/docs/swagger/
3. **Crear tu primer flujo**: Dashboard → Nuevo Flujo → CADMA
4. **Ejecutar un paso**: Seleccionar flujo → Tab Pasos → Ejecutar
5. **Ver logs en tiempo real**: Tab Ejecuciones → Logs streaming
6. **Colaborar en tiempo real**: Abrir flujo en 2 navegadores

---

**¡Listo para empezar!** 🚀

Cualquier duda → Consulta los README específicos o el código fuente.
