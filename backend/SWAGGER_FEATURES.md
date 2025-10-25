# 🧪 ChemFlow Swagger UI - Características

## Descripción General

El Swagger UI de ChemFlow ha sido completamente personalizado con un tema químico profesional e integración de autenticación directa.

## 🎨 Tema Químico Profesional

### Diseño Visual

- **Gradiente de cabecera**: Azul oscuro (#2C3E50) → Azul (#3498DB) → Púrpura (#9B59B6)
- **Iconos químicos**: Emoji de matraz 🧪 como identidad visual
- **Favicon personalizado**: Matraz químico en formato SVG
- **Colores por método HTTP**:
  - GET: Azul claro (#61affe)
  - POST: Verde (#49cc90)
  - PUT: Naranja (#fca130)
  - DELETE: Rojo (#f93e3e)
  - PATCH: Turquesa (#50e3c2)

### Elementos UI Mejorados

- Spinner de carga con animación de molécula rotando
- Tarjetas de operaciones con sombras y bordes suaves
- Botones con efectos hover y transiciones suaves
- Tipografía moderna y legible
- Responsive design para móviles

## 🔐 Sistema de Autenticación Integrado

### Características

1. **Login Modal Integrado**

   - Modal elegante con animación deslizante
   - Formulario de usuario/contraseña
   - Mensajes de error informativos
   - Cancelación con Escape

2. **Gestión de Estado**

   - Token JWT almacenado en `localStorage`
   - Datos de usuario persistentes
   - Indicador visual de estado de autenticación
   - Botón 🔒/🔓 que cambia según el estado

3. **Interceptor de Requests**

   - Token JWT automáticamente agregado a todas las peticiones
   - Header `Authorization: Bearer <token>` inyectado
   - Sin necesidad de copiar/pegar tokens manualmente

4. **Experiencia de Usuario**
   - Click en botón de estado para login/logout
   - Confirmación antes de cerrar sesión
   - Mensaje de bienvenida personalizado
   - Información del usuario visible

### Atajos de Teclado

- **Ctrl+L** (o Cmd+L en Mac): Abrir modal de login rápido
- **Alt+E**: Expandir todas las secciones
- **Escape**: Cerrar modal de login

## 📥 Botones de Descarga

### Opciones Disponibles

1. **Download JSON**

   - Descarga el schema OpenAPI en formato JSON
   - Archivo: `chemflow-api-schema.json`

2. **Download YAML**

   - Descarga el schema OpenAPI en formato YAML
   - Archivo: `chemflow-api-schema.yaml`

3. **View Schema**

   - Abre el schema raw en nueva pestaña
   - Útil para inspección rápida

4. **Expand All**
   - Expande todas las operaciones de API
   - Útil para navegación completa

## 🚀 Uso

### Acceso a Swagger UI

```
http://127.0.0.1:8000/api/docs/swagger/
```

### Login Rápido

1. **Método 1: Click en botón**

   - Click en el botón "🔒 Not Authenticated" en la cabecera
   - Ingresa tus credenciales
   - Click en "🔓 Login"

2. **Método 2: Atajo de teclado**

   - Presiona `Ctrl+L` (Windows/Linux) o `Cmd+L` (Mac)
   - Ingresa credenciales
   - Presiona Enter o click en Login

3. **Método 3: Swagger Authorize**
   - También puedes usar el botón "Authorize" de Swagger
   - Ingresa: `Bearer <tu_token>`

### Credenciales de Demo

```
Username: chemflow_admin
Password: ChemFlow2024!
```

### Después del Login

- El botón cambia a "🔓 chemflow_admin"
- Todas las peticiones incluyen automáticamente el token JWT
- Puedes probar endpoints protegidos sin configuración adicional
- El token persiste entre recargas de página

## 🔧 Configuración Técnica

### Settings de Django

```python
SPECTACULAR_SETTINGS = {
    "TITLE": "🧪 ChemFlow API",
    "VERSION": "1.0.0",
    "COMPONENT_SPLIT_REQUEST": True,
    "SWAGGER_UI_SETTINGS": {
        "docExpansion": "full",  # Expandir todo por defecto
        "persistAuthorization": True,  # Persistir autorización
        "displayOperationId": True,
        "displayRequestDuration": True,
        "filter": True,  # Barra de búsqueda
    },
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "jwtAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        }
    },
    "SECURITY": [{"jwtAuth": []}],
}
```

### Almacenamiento Local

- `chemflow_access_token`: Token JWT de acceso
- `chemflow_user_data`: Datos del usuario (JSON)

### API de Autenticación

```javascript
// Login
POST /api/token/
Body: { "username": "...", "password": "..." }
Response: { "access": "...", "refresh": "...", "user": {...} }

// Las peticiones incluyen automáticamente:
Authorization: Bearer <access_token>
```

## 📊 Características Swagger UI

### Expansión Automática

- Todas las secciones expandidas por defecto
- Fácil navegación sin clicks adicionales
- Modelos de datos visibles inmediatamente

### Filtrado y Búsqueda

- Barra de búsqueda integrada
- Filtrado en tiempo real de endpoints
- Navegación rápida por tags

### Try It Out

- Habilitado por defecto en todos los endpoints
- Formularios pre-llenados con ejemplos
- Respuestas formateadas con syntax highlighting

### Persistencia

- Autorización persiste entre sesiones
- Parámetros de prueba guardados
- Estado de expansión recordado

## 🎯 Beneficios

### Para Desarrolladores

- No necesitas copiar/pegar tokens manualmente
- Login rápido con atajos de teclado
- Estado de autenticación siempre visible
- Workflow más eficiente para pruebas

### Para Testing

- Cambio rápido entre usuarios
- Tokens persistentes durante desarrollo
- Fácil verificación de permisos
- Prueba de endpoints protegidos sin Postman

### Para Documentación

- Interfaz profesional y atractiva
- Tema coherente con la aplicación química
- Descarga fácil de schemas para integración
- Ejemplos y descripciones claras

## 🔍 Debugging

### Console Logs

El Swagger UI incluye logs informativos:

```
🧪 ChemFlow API: Initializing Swagger UI with chemistry theme...
✅ ChemFlow API: Swagger UI loaded successfully
📖 Expanding all API endpoints...
✅ Expanded 45 operations
✅ All header buttons are visible and interactive
💡 Tip: Press Alt+E to expand all sections
🔑 Authentication: Press Ctrl+L to login quickly
```

### Verificar Autenticación

```javascript
// En la consola del navegador
localStorage.getItem("chemflow_access_token");
localStorage.getItem("chemflow_user_data");
```

## 🛠️ Personalización Futura

### Agregar Más Providers

Para agregar soporte de autenticación adicional:

1. Editar `AuthManager.login()` en `swagger_ui.html`
2. Agregar nuevos métodos de autenticación
3. Actualizar UI con opciones adicionales

### Cambiar Tema

Los colores están centralizados en las variables CSS del `<style>`:

```css
.custom-header {
  background: linear-gradient(135deg, #2c3e50 0%, #3498db 50%, #9b59b6 100%);
}
```

### Agregar Funcionalidades

El template es modular y permite agregar:

- Selector de ambiente (dev/staging/prod)
- Histórico de requests
- Bookmarks de endpoints favoritos
- Export de colecciones para Postman

## 📝 Notas Importantes

1. **Seguridad**: Los tokens se almacenan en `localStorage`. En producción considera usar cookies `httpOnly` para mayor seguridad.

2. **Expiración**: Los tokens JWT expiran después de 60 minutos. El usuario deberá volver a loguearse.

3. **Refresh Tokens**: El sistema actual no implementa refresh automático. Se puede agregar en futuras versiones.

4. **CORS**: Asegúrate de que la API permite CORS desde el origen del Swagger UI.

## 🎉 Resultado Final

Un Swagger UI completamente funcional con:

- ✅ Tema químico profesional y atractivo
- ✅ Login integrado sin herramientas externas
- ✅ Autenticación JWT automática
- ✅ Descarga de schemas en múltiples formatos
- ✅ Navegación mejorada con expansión total
- ✅ Atajos de teclado para productividad
- ✅ Responsive y accesible
- ✅ Persistencia de sesión

**¡Disfruta explorando la ChemFlow API!** 🧪✨
