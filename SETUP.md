# Setup ChemFlow - Guía de Instalación

## 🚀 Setup Inicial Automático

### Opción 1: Setup Completo (Recomendado)

```bash
# Navegar al directorio del backend
cd /path/to/flow/backend

# Ejecutar setup completo
python manage.py setup_chemflow
```

Este comando ejecuta automáticamente:

1. **Migraciones** de base de datos
2. **Creación de roles** del sistema
3. **Usuario administrador** principal
4. **Usuarios de ejemplo** para desarrollo
5. **Moléculas iniciales** para testing

### Opción 2: Setup Personalizado

```bash
# Solo migraciones y administrador (mínimo)
python manage.py setup_chemflow --skip-users --skip-molecules

# Recrear datos existentes
python manage.py setup_chemflow --force

# Solo usuarios y moléculas (sin migraciones)
python manage.py setup_chemflow --skip-migrations
```

## 🔧 Setup Manual Paso a Paso

Si prefieres ejecutar cada paso manualmente:

### 1. Aplicar Migraciones

```bash
python manage.py migrate
```

### 2. Crear Roles del Sistema

```bash
python manage.py seed_roles
```

### 3. Crear Usuario Administrador

```bash
# Con valores por defecto
python manage.py create_admin_user

# Personalizado
python manage.py create_admin_user \
  --username admin \
  --email admin@company.com \
  --password MySecurePassword123!
```

### 4. Crear Usuarios de Ejemplo (Opcional)

```bash
# Crear usuarios de desarrollo
python manage.py seed_users

# Recrear usuarios (elimina existentes)
python manage.py seed_users --delete
```

### 5. Crear Moléculas Iniciales (Opcional)

```bash
# Crear moléculas de ejemplo
python manage.py seed_molecules

# Recrear moléculas (elimina existentes)
python manage.py seed_molecules --delete
```

## 📋 Verificación del Setup

### 1. Verificar Base de Datos

```bash
python manage.py dbshell
```

```sql
-- Verificar tablas creadas
.tables

-- Verificar usuarios
SELECT username, email, is_superuser FROM users_user;

-- Verificar moléculas
SELECT name, smiles, created_by_id FROM chemistry_molecule;
```

### 2. Verificar API

```bash
# Iniciar servidor
python manage.py runserver

# Probar endpoints
curl http://localhost:8000/api/health/
curl http://localhost:8000/api/chemistry/molecules/
```

### 3. Verificar Panel de Admin

Navega a: http://localhost:8000/admin/

Credenciales por defecto:

- **Usuario**: `chemflow_admin`
- **Contraseña**: `ChemFlow2024!`

## 🗂️ Estructura de Usuarios Creados

### Usuario Administrador Principal

- **Username**: `chemflow_admin`
- **Email**: `admin@chemflow.local`
- **Roles**: Superusuario
- **Uso**: Migraciones, operaciones del sistema

### Usuarios de Ejemplo (Desarrollo)

- **admin**: Administrador con todos los permisos
- **moderator**: Moderador con permisos de gestión
- **editor**: Editor con permisos de escritura
- **viewer**: Observador con permisos de lectura
- **scientist**: Científico con roles mixtos

## 🧪 Moléculas Iniciales

Se crean moléculas básicas de elementos:

- Carbono `[C]`
- Hidrógeno `[H]`
- Oxígeno `[O]`
- Nitrógeno `[N]`
- Fósforo `[P]`
- Azufre `[S]`

## ⚙️ Variables de Entorno

### Configuración del Motor de Química

```bash
# Usar RDKit (recomendado para producción)
export CHEM_ENGINE=rdkit

# Usar Mock (para desarrollo/testing)
export CHEM_ENGINE=mock
```

### Configuración de Base de Datos

```bash
# SQLite (desarrollo)
# No requiere configuración adicional

# PostgreSQL (producción)
export DATABASE_URL=postgresql://user:pass@localhost:5432/chemflow
```

## 🔐 Consideraciones de Seguridad

### Desarrollo

- Usar credenciales por defecto está OK
- Usar mock engine para tests
- Base de datos SQLite local

### Producción

⚠️ **IMPORTANTE**: Cambiar configuración antes de desplegar:

```bash
# Crear usuario administrador con credenciales seguras
python manage.py create_admin_user \
  --username your_admin \
  --email admin@yourcompany.com \
  --password "YourSecurePassword123!" \
  --force

# Configurar variables de entorno
export DJANGO_SECRET_KEY="your-secret-key"
export DJANGO_DEBUG=False
export CHEM_ENGINE=rdkit
export DATABASE_URL=postgresql://...
```

## 🚨 Troubleshooting

### Error: "No such table: users_user"

```bash
# Aplicar migraciones primero
python manage.py migrate
python manage.py setup_chemflow
```

### Error: "Role 'admin' does not exist"

```bash
# Crear roles primero
python manage.py seed_roles
python manage.py create_admin_user
```

### Error: "Usuario 'chemflow_admin' no encontrado"

```bash
# Crear administrador primero
python manage.py create_admin_user
python manage.py seed_molecules
```

### Error: "RDKit is not available"

```bash
# Instalar RDKit o usar mock
pip install rdkit-pypi
# O cambiar a mock
export CHEM_ENGINE=mock
```

## 📊 Comandos de Monitoreo

### Verificar Estado del Sistema

```bash
# Ver usuarios
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
print(f'Usuarios: {User.objects.count()}')
print(f'Superusuarios: {User.objects.filter(is_superuser=True).count()}')
"

# Ver moléculas
python manage.py shell -c "
from chemistry.models import Molecule, Family
print(f'Moléculas: {Molecule.objects.count()}')
print(f'Familias: {Family.objects.count()}')
"
```

### Logs del Sistema

```bash
# Ver logs de Django
tail -f /path/to/django.log

# Ver logs de chemistry
python manage.py shell -c "
import logging
logger = logging.getLogger('chemistry')
logger.info('Testing chemistry module')
"
```

---

**Última actualización**: Octubre 2025  
**Versión**: 1.0.0
