# ChemFlow Frontend - Documentación

## 📋 Descripción General

ChemFlow Frontend es una aplicación **Angular 20** (standalone components) que proporciona una interfaz web completa para gestionar flujos de trabajo químicos, moléculas, familias y ejecuciones de procesos.

**Características principales:**
- ✅ Dashboard interactivo con múltiples vistas
- ✅ Gestión de flujos de trabajo (create, edit, execute, branch)
- ✅ Explorador de moléculas y familias químicas
- ✅ Canvas visual para diagramas de flujos
- ✅ Ejecución de pasos con streaming de logs
- ✅ Colaboración en tiempo real (WebSocket)
- ✅ Autenticación JWT integrada
- ✅ Notificaciones en tiempo real
- ✅ Sistema de diseño (Design System) con temas claro/oscuro

---

## 🏗️ Arquitectura

### Capas Arquitectónicas

```
┌──────────────────────────────────────────────────────┐
│                  PRESENTACIÓN (Views)                │
│  (Pages, Componentes de negocio)                     │
└──────────────────────────────────────────────────────┘
                         ↕
┌──────────────────────────────────────────────────────┐
│              COMPONENTES REUTILIZABLES               │
│  (Shared Components: Card, Button, Modal, Table)     │
└──────────────────────────────────────────────────────┘
                         ↕
┌──────────────────────────────────────────────────────┐
│                CAPA DE SERVICIOS                     │
│  (Services: API, WebSocket, State Management)        │
└──────────────────────────────────────────────────────┘
                         ↕
┌──────────────────────────────────────────────────────┐
│            SISTEMA DE DISEÑO                         │
│  (Design Tokens, Theme, Animations, Global Styles)  │
└──────────────────────────────────────────────────────┘
                         ↕
┌──────────────────────────────────────────────────────┐
│            BACKEND API (REST + WebSocket)            │
└──────────────────────────────────────────────────────┘
```

### Estructura de Directorios

```
frontend/
├── src/
│   ├── app/
│   │   ├── pages/                           # Páginas (vistas)
│   │   │   ├── flows/
│   │   │   │   ├── flows-list.component.ts
│   │   │   │   ├── flow-detail.component.ts
│   │   │   │   ├── step-catalog.component.ts
│   │   │   │   ├── branch-management.component.ts
│   │   │   │   ├── nodes-viewer.component.ts
│   │   │   │   ├── steps-list.component.ts
│   │   │   │   ├── artifacts.component.ts
│   │   │   │   ├── executions.component.html
│   │   │   │   └── styles/
│   │   │   ├── chemistry/
│   │   │   │   ├── molecule-detail.component.ts
│   │   │   │   ├── family-detail.component.ts
│   │   │   │   ├── create-family.component.ts
│   │   │   │   └── styles/
│   │   │   ├── users/
│   │   │   │   ├── user-detail.component.ts
│   │   │   │   └── styles/
│   │   │   ├── notifications/
│   │   │   │   └── notifications.component.ts
│   │   │   └── styles/                     # Estilos compartidos
│   │   │       └── _variables.scss
│   │   │
│   │   ├── shared/                         # Módulos compartidos
│   │   │   ├── components/                 # Componentes reutilizables
│   │   │   │   ├── button/
│   │   │   │   ├── card/
│   │   │   │   ├── modal/
│   │   │   │   ├── data-table/
│   │   │   │   ├── paginator/
│   │   │   │   ├── badge/
│   │   │   │   ├── skeleton/
│   │   │   │   ├── empty-state/
│   │   │   │   ├── flow-node/
│   │   │   │   ├── flow-canvas/
│   │   │   │   ├── json-viewer/
│   │   │   │   ├── json-input/
│   │   │   │   ├── confirm-dialog/
│   │   │   │   └── layout/
│   │   │   └── design-system/              # Sistema de diseño
│   │   │       ├── design-tokens.ts        # Tokens (colores, spacing)
│   │   │       ├── theme.service.ts        # Gestor de temas
│   │   │       ├── global-styles.scss
│   │   │       ├── animations.scss
│   │   │       └── index.ts
│   │   │
│   │   ├── services/                       # Servicios (lógica, API)
│   │   │   ├── flow.service.ts             # Flows REST API
│   │   │   ├── chemistry.service.ts        # Chemistry REST API
│   │   │   ├── users.service.ts            # Users REST API
│   │   │   ├── flow-collaboration.service.ts  # WebSocket
│   │   │   ├── sse.service.ts              # Server-Sent Events
│   │   │   ├── notifications.service.ts    # Notifications API
│   │   │   ├── ai-recommendation.service.ts # IA suggestions
│   │   │   ├── swagger.service.ts          # OpenAPI schema
│   │   │   ├── chemistry-app.service.ts    # App service (domain logic)
│   │   │   ├── flows-app.service.ts        # App service (domain logic)
│   │   │   └── users-app.service.ts        # App service (domain logic)
│   │   │
│   │   ├── app.component.ts                # Componente raíz
│   │   ├── app.routes.ts                   # Rutas
│   │   ├── config.ts                       # Configuración global
│   │   └── main.ts                         # Bootstrap
│   │
│   ├── index.html
│   └── styles.scss
│
├── angular.json                            # Configuración Angular CLI
├── tsconfig.json                           # Configuración TypeScript
├── package.json                            # Dependencias npm
└── README.md
```

---

## 🔄 Diagrama de Arquitectura de Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                      APP COMPONENT                          │
│                  (Raíz de la aplicación)                    │
└──────────────────────┬──────────────────────────────────────┘
                       │ router-outlet
        ┌──────────────┼──────────────┬────────────┐
        │              │              │            │
        ↓              ↓              ↓            ↓
    ┌────────────┐ ┌─────────┐ ┌──────────┐ ┌──────────────┐
    │ FlowsList  │ │ Chemistry│ │  Users   │ │ Notifications│
    │ Component  │ │ Components  │ Components   │ Component  │
    └─┬──────────┘ └────┬────┘ └────┬─────┘ └──────────────┘
      │ uses            │          │
      ↓                 ↓          ↓
    ┌──────────────────────────────────────────┐
    │         SHARED COMPONENTS               │
    │ (Button, Card, Modal, DataTable,        │
    │  FlowCanvas, FlowNode, etc.)            │
    └──────────┬───────────────────────────────┘
               │ imports
        ┌──────┴──────────────────┐
        │                         │
        ↓                         ↓
    ┌─────────────────┐   ┌──────────────────┐
    │ Design System   │   │   GlobalStyles  │
    │ (tokens, theme) │   │   animations    │
    └─────────────────┘   └──────────────────┘
```

### Flujo de Datos (State Management con Signals)

```
┌─────────────────────────────────────┐
│   Component Template (HTML)         │
│   (User Actions: Click, Input)      │
└──────────────┬──────────────────────┘
               │
               ↓
┌──────────────────────────────────────────┐
│   Component TypeScript                   │
│   - signal<T>() = estado reactivo        │
│   - computed() = estado derivado         │
│   - effect() = side effects              │
└──────────────┬───────────────────────────┘
               │
               ↓
┌──────────────────────────────────────────┐
│   Service (Ej: FlowService)              │
│   - Observable<T> del HTTP/WebSocket     │
│   - Lógica de transformación             │
└──────────────┬───────────────────────────┘
               │
               ↓
┌──────────────────────────────────────────┐
│   HttpClient / WebSocket                 │
│   → Backend REST API / WS                │
└──────────────────────────────────────────┘
```

---

## 📦 Componentes Principales

### 1. FlowsListComponent
**Path**: `pages/flows/flows-list.component.ts`

Muestra lista de flujos con opciones para crear, ejecutar y seleccionar.

```typescript
export class FlowsListComponent {
  flows = signal<Flow[]>([]);
  loading = signal(false);
  error = signal<string | null>(null);
  currentPage = signal(1);
  pageSize = signal(20);
  
  // Crea flujo desde definición
  createFlowFromDefinition(defKey: string, name: string)
  
  // Carga todos los flujos del usuario
  loadFlows()
}
```

**Interacciones:**
- `GET /api/flows/` → Carga lista
- `POST /api/flows/` → Crea nuevo flujo
- Navega a `FlowDetailComponent` en click

---

### 2. FlowDetailComponent
**Path**: `pages/flows/flow-detail/flow-detail.component.ts`

Vista detallada de un flujo con tabs para diferentes vistas.

```typescript
export class FlowDetailComponent {
  flowId = signal<number | null>(null);
  flow = signal<any>(null);
  currentTab = signal<'overview' | 'steps' | 'executions' | 'branches'>('overview');
  
  // Tab: Overview
  // Tab: Steps & Step Catalog
  // Tab: Executions
  // Tab: Branches
}
```

**Tabs:**
1. **Overview**: Información general del flujo
2. **Steps**: Pasos definidos, dependencies
3. **Executions**: Histórico de ejecuciones
4. **Branches**: Ramas del flujo (árbol sin merge)

---

### 3. FlowCanvasComponent
**Path**: `shared/components/flow-canvas/flow-canvas.component.ts`

Canvas interactivo para visualizar y editar flujos.

```typescript
export class FlowCanvasComponent {
  nodes = signal<FlowNode[]>([]);
  edges = signal<FlowEdge[]>([]);
  selectedNode = signal<FlowNode | null>(null);
  zoom = signal(1);
  pan = signal({ x: 0, y: 0 });
  
  // Drag & drop de nodos
  onNodeDragStart(node: FlowNode)
  
  // Crear conexión entre nodos
  createEdge(fromNodeId: string, toNodeId: string)
  
  // Zoom y pan
  zoomIn() / zoomOut()
  panTo(x: number, y: number)
  
  // Undo/Redo basado en eventos
  undo() / redo()
}
```

---

### 4. StepCatalogComponent
**Path**: `pages/flows/step-catalog/step-catalog.component.ts`

Catálogo de pasos disponibles con búsqueda y filtrado.

```typescript
export class StepCatalogComponent {
  steps = signal<any[]>([]);
  selectedStep = signal<any | null>(null);
  searchQuery = signal('');
  filterType = signal<string | null>(null);
  
  // Busca y filtra pasos
  searchSteps(query: string)
  
  // Muestra detalle de paso
  selectStep(step: any)
  
  // Agregar paso a flujo
  addStepToFlow(step: any)
}
```

---

### 5. ExecutionsComponent
**Path**: `pages/flows/executions/executions.component.ts`

Vista de ejecuciones de un flujo con detalles y logs.

```typescript
export class ExecutionsComponent {
  executions = signal<any[]>([]);
  selectedExecution = signal<any | null>(null);
  
  // Carga historial de ejecuciones
  loadExecutions()
  
  // SSE streaming de logs de un step
  watchStepExecutionLogs(stepExecutionId: number)
}
```

---

### 6. DataTableComponent
**Path**: `shared/components/data-table/data-table.component.ts`

Tabla genérica reutilizable para mostrar datos.

```typescript
@Component({
  selector: 'app-data-table',
  inputs: ['columns', 'data', 'loading'],
  outputs: ['rowClicked', 'pageChanged']
})
export class DataTableComponent {
  @Input() columns: TableColumn[];
  @Input() data: any[] = [];
  @Input() loading = false;
  @Input() emptyMessage = 'Sin datos';
  
  @Output() rowClicked = new EventEmitter<any>();
  @Output() pageChanged = new EventEmitter<number>();
}
```

---

### 7. ModalComponent
**Path**: `shared/components/modal/modal.component.ts`

Modal reutilizable para diálogos.

```typescript
@Component({
  selector: 'app-modal',
  inputs: ['visible', 'title', 'size'],
  outputs: ['close']
})
export class ModalComponent {
  @Input() visible = false;
  @Input() title = '';
  @Input() size: 'small' | 'medium' | 'large' = 'medium';
  @Output() close = new EventEmitter<void>();
}
```

---

## 🎨 Sistema de Diseño

### Design Tokens

```typescript
// Colores
const colors = {
  primary: '#2b6cb0',
  secondary: '#edf2f7',
  accent: '#38a169',
  danger: '#e53e3e',
  success: '#48bb78'
};

// Spacing (escala 4px)
const spacing = {
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px'
};

// Typography
const typography = {
  h1: { size: '32px', weight: 700 },
  h2: { size: '24px', weight: 700 },
  body: { size: '16px', weight: 400 }
};
```

### Temas (Claro/Oscuro)

```typescript
// En theme.service.ts
themeMode = signal<'light' | 'dark'>('light');

toggleTheme() {
  const newMode = this.themeMode() === 'light' ? 'dark' : 'light';
  this.themeMode.set(newMode);
  document.documentElement.setAttribute('data-theme', newMode);
  localStorage.setItem('theme', newMode);
}
```

---

## 🔌 Servicios Principales

### FlowService
Gestión de flujos REST API.

```typescript
@Injectable({ providedIn: 'root' })
export class FlowService {
  getFlows(params?: any): Observable<{ results: Flow[]; count: number }>
  getFlow(id: number): Observable<Flow>
  createFlow(flow: Partial<Flow>): Observable<Flow>
  executeStep(flowId: number, stepId: number, params: any): Observable<any>
  getSteps(flowId: number): Observable<Step[]>
  getExecutions(flowId: number): Observable<any[]>
  createBranch(flowId: number): Observable<any>
}
```

### ChemistryService
Gestión de moléculas y familias.

```typescript
@Injectable({ providedIn: 'root' })
export class ChemistryService {
  getMolecules(params?: any): Observable<{ results: Molecule[]; count: number }>
  getMolecule(id: number): Observable<Molecule>
  createMolecule(molecule: Partial<Molecule>): Observable<Molecule>
  getFamilies(params?: any): Observable<{ results: Family[]; count: number }>
  getFamily(id: number): Observable<Family>
  createFamilyFromSmiles(name: string, smilesList: string[]): Observable<Family>
}
```

### FlowCollaborationService
WebSocket para colaboración en tiempo real.

```typescript
@Injectable({ providedIn: 'root' })
export class FlowCollaborationService {
  connect(flowId: number): void
  disconnect(): void
  broadcastNodeChange(nodeId: string, position: any): void
  onNodeChanged$: Observable<any>
  onCursorMoved$: Observable<any>
  onLockChanged$: Observable<any>
}
```

### SseService
Server-Sent Events para streaming de logs.

```typescript
@Injectable({ providedIn: 'root' })
export class SseService {
  openStepExecutionLogs(
    stepExecutionId: number,
    onMessage: (msg: SseMessage) => void
  ): EventSource
  
  close(stepExecutionId: number): void
}
```

---

## 🔐 Autenticación

### AuthService
Gestión de JWT.

```typescript
login(username: string, password: string): Observable<{ access: string; refresh: string }>

logout(): void

refreshToken(): Observable<{ access: string }>

isAuthenticated(): boolean

getToken(): string | null
```

### Interceptor HTTP
Añade token JWT automáticamente a todos los requests.

```typescript
@Injectable()
export class JwtInterceptor implements HttpInterceptor {
  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    const token = this.authService.getToken();
    if (token) {
      req = req.clone({
        setHeaders: { Authorization: `Bearer ${token}` }
      });
    }
    return next.handle(req);
  }
}
```

---

## 📡 Comunicación en Tiempo Real

### WebSocket (Colaboración)
```typescript
// Conectar a flujo
collaborationService.connect(flowId);

// Escuchar cambios
collaborationService.onNodeChanged$.subscribe(event => {
  // Refrescar nodo en canvas
});

// Enviar cambio
collaborationService.broadcastNodeChange(nodeId, { x: 100, y: 200 });
```

### SSE (Logs de Ejecución)
```typescript
// Abrir stream
const eventSource = sseService.openStepExecutionLogs(stepExecutionId, (msg) => {
  console.log('Log:', msg.data);
});

// Cerrar stream
sseService.close(stepExecutionId);
```

---

## 🚀 Comandos de Desarrollo

### Instalación
```bash
cd frontend
npm install
```

### Desarrollo
```bash
npm start
# http://localhost:4200
```

### Build
```bash
npm run build
# Salida en dist/
```

### Tests
```bash
npm test
# Karma + Jasmine
```

### Lint
```bash
ng lint
# ESLint
```

### Generar API desde OpenAPI
```bash
npm run generate:api
# Genera clients en src/app/api/
# Requiere: ChemFlow API.yaml
```

---

## 📦 Dependencias Principales

```json
{
  "@angular/core": "^20.0.0",
  "@angular/router": "^20.0.0",
  "@angular/forms": "^20.0.0",
  "rxjs": "~7.8.0"
}
```

**Dev:**
```json
{
  "@angular/cli": "^20.0.5",
  "typescript": "~5.8.2",
  "@openapitools/openapi-generator-cli": "^2.13.4"
}
```

---

## 🎯 Patrones & Best Practices

### 1. Standalone Components
```typescript
@Component({
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: '...'
})
export class MyComponent {}
```

### 2. Signals (Angular 17+)
```typescript
count = signal(0);
increment() { this.count.update(v => v + 1); }
```

### 3. Computed
```typescript
doubleCount = computed(() => this.count() * 2);
```

### 4. Effect
```typescript
constructor() {
  effect(() => {
    console.log('Count changed:', this.count());
  });
}
```

### 5. Observables & RxJS
```typescript
data$ = this.flowService.getFlows().pipe(
  catchError(err => of([])),
  shareReplay(1)
);
```

---

## 📂 Estructura CSS/SCSS

### Global
```scss
// global-styles.scss
@import "./design-tokens-css.scss";

:root {
  --primary-color: #2b6cb0;
  --spacing-md: 16px;
}
```

### Por página
```scss
// pages/flows/flows-list.component.scss
@use "../../styles/_variables.scss" as *;

.flows-list {
  padding: $space-md;
  display: flex;
}
```

### Componentes compartidos
```scss
// shared/components/button/button.component.scss
.btn {
  padding: $space-sm $space-md;
  border-radius: 4px;
  font-weight: 500;
}
```

---

## 🧪 Testing

### Unit Tests
```typescript
describe('FlowService', () => {
  let service: FlowService;
  
  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(FlowService);
  });
  
  it('should fetch flows', () => {
    service.getFlows().subscribe(result => {
      expect(result.results).toBeDefined();
    });
  });
});
```

### Component Tests
```typescript
describe('FlowsListComponent', () => {
  let component: FlowsListComponent;
  let fixture: ComponentFixture<FlowsListComponent>;
  
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FlowsListComponent]
    }).compileComponents();
    
    fixture = TestBed.createComponent(FlowsListComponent);
    component = fixture.componentInstance;
  });
  
  it('should display flows', () => {
    expect(component.flows().length).toBe(0);
  });
});
```

---

## 📖 Configuración TypeScript

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "strict": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "sourceMap": true
  }
}
```

---

## 🔗 Referencias

- [Angular 20 Docs](https://angular.io/docs)
- [Angular Signals](https://angular.io/guide/signals)
- [RxJS](https://rxjs.dev/)
- [TypeScript](https://www.typescriptlang.org/)
- [SASS](https://sass-lang.com/)

---

## 🤝 Contribución

1. Crear rama: `git checkout -b feature/nombre`
2. Cambios + componentes
3. Tests: `ng test`
4. Lint: `ng lint`
5. Commit: `git commit -am 'feat: descripción'`
6. Push + PR

---

## 📄 Licencia

MIT License - Ver [LICENSE](../LICENSE) para más detalles.

Este proyecto está bajo la licencia MIT, la cual es altamente permisiva y permite:
- ✅ Uso comercial
- ✅ Modificación
- ✅ Distribución
- ✅ Uso privado
- ⚠️ Con la única condición de incluir la licencia y copyright
