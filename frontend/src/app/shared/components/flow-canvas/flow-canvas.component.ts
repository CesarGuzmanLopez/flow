/**
 * Flow Canvas Component - Editor visual de flujos
 *
 * Proporciona:
 * - Canvas interactivo para diagramas
 * - Drag & drop de nodos
 * - Conexiones visuales entre nodos
 * - Zoom y pan
 * - Grid de posicionamiento
 * - Undo/redo basado en eventos
 */

import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  computed,
  inject,
  OnDestroy,
  OnInit,
  signal,
} from '@angular/core';
import {
  FlowCollaborationService,
  UserPresence,
} from '../../../services/flow-collaboration.service';
import { ButtonComponent } from '../button/button.component';
import { FlowNodeConfig } from '../flow-node/flow-node.component';

interface FlowEdge {
  id: string;
  fromNodeId: string;
  toNodeId: string;
}

@Component({
  selector: 'app-flow-canvas',
  standalone: true,
  imports: [CommonModule, ButtonComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="flow-canvas-container">
      <!-- Toolbar -->
      <div class="canvas-toolbar">
        <div class="toolbar-left">
          <app-button variant="tertiary" size="sm" (click)="addNode()"
            >+ Nodo</app-button
          >
          <app-button
            variant="ghost"
            size="sm"
            (click)="undo()"
            [disabled]="!canUndo()"
            >↶ Deshacer</app-button
          >
          <app-button
            variant="ghost"
            size="sm"
            (click)="redo()"
            [disabled]="!canRedo()"
            >↷ Rehacer</app-button
          >
        </div>
        <div class="toolbar-right">
          <span>Zoom: {{ (zoomLevel() * 100).toFixed(0) }}%</span>
          <app-button
            variant="ghost"
            size="sm"
            (click)="decreaseZoom()"
            [disabled]="zoomLevel() <= 0.5"
            >−</app-button
          >
          <app-button
            variant="ghost"
            size="sm"
            (click)="increaseZoom()"
            [disabled]="zoomLevel() >= 2"
            >+</app-button
          >
          <app-button variant="ghost" size="sm" (click)="fitToView()"
            >Ajustar</app-button
          >
        </div>
      </div>

      <!-- Canvas SVG para conexiones -->
      <svg
        class="canvas-svg"
        [attr.viewBox]="'0 0 ' + canvasWidth() + ' ' + canvasHeight()"
      >
        <defs>
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="7"
            refX="9"
            refY="3.5"
            orient="auto"
          >
            <polygon points="0 0, 10 3.5, 0 7" fill="var(--accent-primary)" />
          </marker>
          <marker
            id="arrowhead-dash"
            markerWidth="10"
            markerHeight="7"
            refX="9"
            refY="3.5"
            orient="auto"
          >
            <polygon points="0 0, 10 3.5, 0 7" fill="var(--state-warning)" />
          </marker>
        </defs>

        <!-- Líneas de conexión -->
        <g class="edges">
          <path
            *ngFor="let edge of edges()"
            class="edge"
            [attr.d]="getEdgePath(edge)"
            [attr.marker-end]="'url(#arrowhead)'"
          />
        </g>
      </svg>

      <!-- Canvas de nodos -->
      <div
        class="canvas-nodes"
        [style.transform]="'scale(' + zoomLevel() + ')'"
      >
        <div
          *ngFor="let node of nodes()"
          class="node-wrapper"
          [style.left.px]="node.x || 0"
          [style.top.px]="node.y || 0"
          [class.selected]="selectedNodeId() === node.id"
          (mousedown)="startDrag($event, node)"
          (click)="selectNode(node.id)"
        >
          <div class="node-box">
            <div class="node-header-simple">{{ node.title }}</div>
            <div class="node-type">{{ getNodeTypeName(node.type) }}</div>
          </div>
        </div>
      </div>

      <!-- Properties Panel (derecha) -->
      <div
        class="properties-panel"
        *ngIf="selectedNodeId() && getSelectedNode() as node"
      >
        <div class="panel-header">
          <h3>Propiedades</h3>
          <button (click)="selectedNodeId.set(null)" class="close-btn">
            ✕
          </button>
        </div>
        <div class="panel-content">
          <div class="prop-group">
            <label>Título</label>
            <input
              [value]="node.title"
              (change)="onTitleChange($event)"
              class="prop-input"
            />
          </div>
          <div class="prop-group">
            <label>Tipo</label>
            <select
              [value]="node.type"
              (change)="onTypeChange($event)"
              class="prop-input"
            >
              <option value="start">Inicio</option>
              <option value="step">Paso</option>
              <option value="decision">Decisión</option>
              <option value="end">Fin</option>
              <option value="join">Unir</option>
              <option value="split">Dividir</option>
            </select>
          </div>
          <div class="prop-group">
            <label>Descripción</label>
            <textarea
              [value]="node.description || ''"
              (change)="onDescriptionChange($event)"
              class="prop-input"
            ></textarea>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      .flow-canvas-container {
        display: grid;
        grid-template-columns: 1fr 300px;
        grid-template-rows: 60px 1fr;
        height: 100%;
        background: var(--bg-primary);
        border: 1px solid var(--border-light);
        border-radius: 8px;
        overflow: hidden;
      }

      /* Toolbar */
      .canvas-toolbar {
        grid-column: 1 / -1;
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 16px;
        background: var(--bg-secondary);
        border-bottom: 1px solid var(--border-light);
        gap: 16px;

        .toolbar-left,
        .toolbar-right {
          display: flex;
          gap: 8px;
          align-items: center;
        }

        span {
          font-size: 12px;
          color: var(--text-tertiary);
          min-width: 80px;
          text-align: center;
        }
      }

      /* Canvas SVG */
      .canvas-svg {
        grid-column: 1;
        grid-row: 2;
        width: 100%;
        height: 100%;
        background: linear-gradient(
          90deg,
          transparent 24%,
          var(--border-light) 25%,
          var(--border-light) 26%,
          transparent 27%,
          transparent 74%,
          var(--border-light) 75%,
          var(--border-light) 76%,
          transparent 77%,
          transparent
        );
        background-size: 40px 40px;
        cursor: grab;

        &:active {
          cursor: grabbing;
        }

        .edges {
          fill: none;
          stroke: var(--accent-secondary);
          stroke-width: 2;
        }

        .edge {
          opacity: 0.7;
          transition: opacity 200ms ease-out;

          &:hover {
            opacity: 1;
            stroke-width: 3;
          }

          &.edge-creating {
            stroke: var(--state-warning);
            stroke-dasharray: 5, 5;
            opacity: 0.8;
          }
        }

        .edge-temp {
          stroke: var(--state-warning);
          stroke-width: 2;
          stroke-dasharray: 5, 5;
          opacity: 0.6;
        }
      }

      /* Canvas de nodos */
      .canvas-nodes {
        grid-column: 1;
        grid-row: 2;
        position: relative;
        width: 100%;
        height: 100%;
        transform-origin: 0 0;
        transition: transform 300ms ease-out;

        .node-wrapper {
          position: absolute;
          width: 180px;
          cursor: grab;
          transition: all 300ms ease-out;

          &:active {
            cursor: grabbing;
            z-index: 50;
          }

          &.selected {
            z-index: 40;

            .node-box {
              border-color: var(--accent-primary);
              box-shadow: 0 0 0 3px rgba(70, 130, 180, 0.2);
            }
          }

          .node-box {
            background: var(--bg-secondary);
            border: 2px solid var(--border-light);
            border-radius: 8px;
            padding: 12px;
            text-align: center;
            cursor: pointer;
            transition: all 300ms ease-out;
            box-shadow: var(--shadow-md);

            &:hover {
              box-shadow: var(--shadow-lg);
              transform: translateY(-2px);
            }

            .node-header-simple {
              font-weight: 700;
              font-size: 13px;
              color: var(--text-primary);
              margin-bottom: 6px;
              word-break: break-word;
            }

            .node-type {
              font-size: 10px;
              font-weight: 600;
              color: var(--text-tertiary);
              text-transform: uppercase;
              padding: 4px;
              background: var(--bg-tertiary);
              border-radius: 3px;
            }
          }
        }
      }

      /* Properties Panel */
      .properties-panel {
        grid-column: 2;
        grid-row: 2;
        display: flex;
        flex-direction: column;
        background: var(--bg-secondary);
        border-left: 1px solid var(--border-light);
        overflow-y: auto;
        animation: slideInRight 300ms ease-out;

        @keyframes slideInRight {
          from {
            transform: translateX(100%);
          }
          to {
            transform: translateX(0);
          }
        }

        .panel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px;
          border-bottom: 1px solid var(--border-light);

          h3 {
            margin: 0;
            font-size: 14px;
            font-weight: 600;
          }

          .close-btn {
            background: none;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            font-size: 16px;
            padding: 0;
            transition: color 200ms ease-out;

            &:hover {
              color: var(--text-primary);
            }
          }
        }

        .panel-content {
          flex: 1;
          padding: 16px;
          overflow-y: auto;

          .prop-group {
            margin-bottom: 16px;

            label {
              display: block;
              font-size: 12px;
              font-weight: 600;
              color: var(--text-secondary);
              margin-bottom: 4px;
              text-transform: uppercase;
            }

            .prop-input {
              width: 100%;
              padding: 8px;
              font-size: 13px;
              background: var(--bg-primary);
              border: 1px solid var(--border-light);
              border-radius: 4px;
              color: var(--text-primary);
              font-family: inherit;
              transition: border-color 200ms ease-out;

              &:focus {
                outline: none;
                border-color: var(--accent-primary);
              }
            }

            textarea {
              min-height: 80px;
              resize: vertical;
            }
          }
        }
      }

      /* Responsive */
      @media (max-width: 1024px) {
        .flow-canvas-container {
          grid-template-columns: 1fr;

          .properties-panel {
            grid-column: 1;
            position: absolute;
            right: 0;
            top: 60px;
            width: 250px;
            height: calc(100% - 60px);
            border-left: 1px solid var(--border-light);
            box-shadow: -4px 0 12px rgba(0, 0, 0, 0.1);
            z-index: 100;
          }
        }
      }
    `,
  ],
})
export class FlowCanvasComponent implements OnInit, OnDestroy {
  // Services
  private collaborationService = inject(FlowCollaborationService);
  private cdr = inject(ChangeDetectorRef);

  // State
  nodes = signal<FlowNodeConfig[]>([]);
  edges = signal<FlowEdge[]>([]);
  selectedNodeId = signal<string | null>(null);
  zoomLevel = signal(1);
  canvasWidth = signal(1200);
  canvasHeight = signal(600);
  mouseX = signal(0);
  mouseY = signal(0);

  // Colaboración
  remoteUsers = signal<UserPresence[]>([]);
  isCollaborating = signal(false);
  private flowId = 1; // Este valor debe venir de Input @Input
  // Undo/redo history
  private history = signal<FlowNodeConfig[][]>([[]]);
  private historyIndex = signal(0);

  // Flags
  creatingEdge = signal<{
    fromId: string;
    fromX: number;
    fromY: number;
  } | null>(null);
  canUndo = computed(() => this.historyIndex() > 0);
  canRedo = computed(() => this.historyIndex() < this.history().length - 1);

  ngOnInit() {
    // Inicializar con nodos de ejemplo
    this.addExampleNodes();
    window.addEventListener('mousemove', (e) => this.onMouseMove(e));

    // Iniciar colaboración si está configurada
    this.startCollaboration();

    // Suscribirse a cambios remotos
    this.collaborationService.nodeChanged$.subscribe((change: any) => {
      this.handleRemoteNodeChange(change);
    });

    this.collaborationService.elementLocked$.subscribe((lock: any) => {
      console.log(`Elemento ${lock.element_id} lockeado por ${lock.username}`);
    });

    this.remoteUsers = this.collaborationService.remoteUsers;
  }

  ngOnDestroy() {
    // Detener colaboración
    this.collaborationService.disconnect();
    window.removeEventListener('mousemove', (e) => this.onMouseMove(e));
  }

  /**
   * Iniciar colaboración en tiempo real
   */
  private startCollaboration(): void {
    try {
      this.collaborationService.connect(this.flowId, 1, 'Usuario1');
      this.isCollaborating.set(true);
    } catch (error) {
      console.error('Error iniciando colaboración:', error);
      this.isCollaborating.set(false);
    }
  }

  /**
   * Manejar cambios de nodos remotos
   */
  private handleRemoteNodeChange(change: any): void {
    const { node_id, node_data, operation } = change;

    if (operation === 'create') {
      this.nodes.update((n) => [...n, node_data]);
    } else if (operation === 'update') {
      this.nodes.update((n) =>
        n.map((node) => (node.id === node_id ? node_data : node))
      );
    } else if (operation === 'delete') {
      this.nodes.update((n) => n.filter((node) => node.id !== node_id));
    }
  }

  /**
   * Obtener nombre del tipo de nodo
   */
  getNodeTypeName(type: string): string {
    const typeNames: Record<string, string> = {
      start: 'Inicio',
      step: 'Paso',
      decision: 'Decisión',
      end: 'Fin',
      join: 'Unir',
      split: 'Dividir',
    };
    return typeNames[type] || 'Paso';
  }

  /**
   * Handlers para cambios en propiedades
   */
  onTitleChange(event: Event): void {
    const value = (event.target as HTMLInputElement).value;
    this.updateNodeProperties({ title: value });
  }

  onTypeChange(event: Event): void {
    const value = (event.target as HTMLSelectElement).value;
    this.updateNodeProperties({ type: value as any });
  }

  onDescriptionChange(event: Event): void {
    const value = (event.target as HTMLTextAreaElement).value;
    this.updateNodeProperties({ description: value });
  }

  /**
   * Agregar nodo de ejemplo
   */
  addNode(): void {
    const newNode: FlowNodeConfig = {
      id: `node-${Date.now()}`,
      title: 'Nuevo Paso',
      type: 'step',
      x: Math.random() * 400,
      y: Math.random() * 300,
    };
    this.nodes.update((n) => [...n, newNode]);
    this.saveToHistory();

    // Propagar cambio a otros usuarios
    if (this.isCollaborating()) {
      this.collaborationService.broadcastNodeChange(
        newNode.id,
        newNode,
        'create'
      );
    }
  }

  /**
   * Eliminar nodo
   */
  deleteNode(nodeId: string): void {
    this.nodes.update((n) => n.filter((node) => node.id !== nodeId));
    this.edges.update((e) =>
      e.filter((edge) => edge.fromNodeId !== nodeId && edge.toNodeId !== nodeId)
    );
    if (this.selectedNodeId() === nodeId) {
      this.selectedNodeId.set(null);
    }
    this.saveToHistory();

    // Propagar cambio a otros usuarios
    if (this.isCollaborating()) {
      this.collaborationService.broadcastNodeChange(nodeId, null, 'delete');
    }
  }

  /**
   * Seleccionar nodo
   */
  selectNode(nodeId: string): void {
    this.selectedNodeId.set(nodeId);

    // Notificar selección a otros usuarios
    if (this.isCollaborating()) {
      this.collaborationService.broadcastNodeSelection(nodeId);
    }
  }

  /**
   * Editar nodo
   */
  editNode(nodeId: string): void {
    const node = this.nodes().find((n) => n.id === nodeId);
    if (node) {
      const newTitle = prompt('Nuevo título:', node.title);
      if (newTitle) {
        this.nodes.update((n) =>
          n.map((node) =>
            node.id === nodeId ? { ...node, title: newTitle } : node
          )
        );
        this.saveToHistory();
      }
    }
  }

  /**
   * Obtener nodo seleccionado
   */
  getSelectedNode(): FlowNodeConfig | undefined {
    return this.nodes().find((n) => n.id === this.selectedNodeId());
  }

  /**
   * Actualizar propiedades del nodo
   */
  updateNodeProperties(updates: Partial<FlowNodeConfig>): void {
    const selectedNode = this.getSelectedNode();
    if (selectedNode) {
      const updatedNode = { ...selectedNode, ...updates };

      this.nodes.update((n) =>
        n.map((node) =>
          node.id === this.selectedNodeId() ? updatedNode : node
        )
      );
      this.saveToHistory();

      // Propagar cambio a otros usuarios
      if (this.isCollaborating()) {
        this.collaborationService.broadcastNodeChange(
          selectedNode.id,
          updatedNode,
          'update'
        );
      }
    }
  }

  /**
   * Conectar nodos
   */
  onNodeConnect(data: { from: string; to: string }): void {
    const newEdge: FlowEdge = {
      id: `edge-${Date.now()}`,
      fromNodeId: data.from,
      toNodeId: data.to,
    };
    this.edges.update((e) => [...e, newEdge]);
    this.saveToHistory();
  }

  /**
   * Generar path SVG para edge (Bezier curve)
   */
  getEdgePath(edge: FlowEdge): string {
    const fromNode = this.nodes().find((n) => n.id === edge.fromNodeId);
    const toNode = this.nodes().find((n) => n.id === edge.toNodeId);

    if (!fromNode || !toNode) return '';

    const fromX = (fromNode.x || 0) + 100; // Ancho aproximado del nodo
    const fromY = (fromNode.y || 0) + 50;
    const toX = toNode.x || 0;
    const toY = (toNode.y || 0) + 50;

    const controlX = (fromX + toX) / 2;
    const controlY = fromY + (toY - fromY) / 2;

    return `M ${fromX} ${fromY} Q ${controlX} ${controlY} ${toX} ${toY}`;
  }

  /**
   * Zoom
   */
  increaseZoom(): void {
    this.zoomLevel.update((z) => Math.min(z + 0.2, 2));
  }

  decreaseZoom(): void {
    this.zoomLevel.update((z) => Math.max(z - 0.2, 0.5));
  }

  fitToView(): void {
    this.zoomLevel.set(1);
  }

  /**
   * Drag & drop
   */
  startDrag(event: MouseEvent, node: FlowNodeConfig): void {
    const startX = event.clientX;
    const startY = event.clientY;
    const startNodeX = node.x || 0;
    const startNodeY = node.y || 0;

    const onMove = (moveEvent: MouseEvent) => {
      const deltaX = moveEvent.clientX - startX;
      const deltaY = moveEvent.clientY - startY;

      this.nodes.update((n) =>
        n.map((n) =>
          n.id === node.id
            ? {
                ...n,
                x: startNodeX + deltaX / this.zoomLevel(),
                y: startNodeY + deltaY / this.zoomLevel(),
              }
            : n
        )
      );
    };

    const onEnd = () => {
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onEnd);
      this.saveToHistory();
    };

    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onEnd);
  }

  /**
   * Mouse tracking
   */
  onMouseMove(event: MouseEvent): void {
    this.mouseX.set(event.clientX);
    this.mouseY.set(event.clientY);
  }

  /**
   * Undo/Redo
   */
  undo(): void {
    if (this.canUndo()) {
      this.historyIndex.update((h) => h - 1);
      this.nodes.set(
        JSON.parse(JSON.stringify(this.history()[this.historyIndex()]))
      );
    }
  }

  redo(): void {
    if (this.canRedo()) {
      this.historyIndex.update((h) => h + 1);
      this.nodes.set(
        JSON.parse(JSON.stringify(this.history()[this.historyIndex()]))
      );
    }
  }

  private saveToHistory(): void {
    const current = JSON.parse(JSON.stringify(this.nodes()));
    this.history.update((h) => [
      ...h.slice(0, this.historyIndex() + 1),
      current,
    ]);
    this.historyIndex.update((h) => h + 1);
  }

  /**
   * Agregar nodos de ejemplo
   */
  private addExampleNodes(): void {
    const exampleNodes: FlowNodeConfig[] = [
      {
        id: 'node-1',
        title: 'Inicio del Flujo',
        description: 'Punto de entrada',
        type: 'start',
        status: 'pending',
        x: 100,
        y: 50,
      },
      {
        id: 'node-2',
        title: 'Procesar Datos',
        description: 'Procesar información',
        type: 'step',
        x: 100,
        y: 200,
        aiSuggested: true,
      },
      {
        id: 'node-3',
        title: 'Validar Resultado',
        type: 'decision',
        x: 100,
        y: 350,
      },
    ];
    this.nodes.set(exampleNodes);
  }
}
