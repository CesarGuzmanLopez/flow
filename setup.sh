#!/bin/bash

# ChemFlow - Script de inicialización rápida
# Este script configura el proyecto completo desde cero

set -e  # Salir si hay errores

echo "🚀 Iniciando setup de ChemFlow..."

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Verificar que estamos en la raíz del proyecto
if [ ! -f "README.md" ]; then
    echo "❌ Error: Este script debe ejecutarse desde la raíz del proyecto"
    exit 1
fi

echo -e "${BLUE}📦 Paso 1: Configurando entorno virtual Python...${NC}"
if [ ! -d ".venv" ]; then
    echo "✓ Entorno virtual creado con virtualenv"
fi

pip install --upgrade pip
pip install -r backend/requirements.txt
echo "✓ Dependencias Python instaladas"

echo -e "${BLUE}🗄️  Paso 3: Configurando base de datos...${NC}"
cd backend
python manage.py makemigrations users
python manage.py makemigrations flows
python manage.py makemigrations chemistry
python manage.py migrate
echo "✓ Migraciones aplicadas"

echo -e "${BLUE}👤 Paso 4: Creando superusuario...${NC}"
echo "Ingresa los datos del superusuario:"
python manage.py createsuperuser

cd ..

echo -e "${BLUE}📦 Paso 5: Instalando dependencias frontend...${NC}"
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
    echo "✓ Dependencias Node instaladas"
else
    echo "✓ node_modules ya existe"
fi
cd ..

echo -e "${GREEN}✅ ¡Setup completado!${NC}"
echo ""
echo "Para iniciar el proyecto:"
echo ""
echo "  Backend (Terminal 1):"
echo "    cd backend"
echo "    python manage.py runserver"
echo ""
echo "  Frontend (Terminal 2):"
echo "    cd frontend"
echo "    ng serve"
echo ""
echo "Luego abre:"
echo "  - Frontend: http://localhost:4200"
echo "  - Backend API: http://127.0.0.1:8000"
echo "  - Admin: http://127.0.0.1:8000/admin"
echo "  - Swagger: http://127.0.0.1:8000/api/docs/swagger/"
echo ""
echo "🎉 ¡Feliz desarrollo!"
