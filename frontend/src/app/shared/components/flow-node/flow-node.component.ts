/**
 * Flow Node Component - Nodo base para diagramas de flujos
 *
 * Renderiza un nodo interactivo con soporte para:
 * - Conexiones (entrada/salida)
 * - Drag & drop
 * - Estados visuales
 * - IA-suggested markers
 */

import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  HostListener,
  Input,
  Output,
  signal,
} from '@angular/core';
import { CardComponent } from '../card/card.component';

export interface FlowNodeConfig {
  id: string;
  title: string;
  description?: string;
  type: 'start' | 'step' | 'decision' | 'end' | 'join' | 'split';
  status?: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  aiSuggested?: boolean;
  draggable?: boolean;
  selected?: boolean;
  x?: number;
  y?: number;
}

@Component({
  selector: 'app-flow-node',
  standalone: true,
  imports: [CommonModule, CardComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div
      class="flow-node"
      [class.selected]="selected()"
      [style.left.px]="x()"
      [style.top.px]="y()"
    >
      <!-- Marker IA (si aplica) -->
      <div
        *ngIf="config().aiSuggested"
        class="ai-marker"
        title="Sugerencia de IA"
      >
        <span class="ai-label">IA</span>
      </div>

      <!-- Conectores entrada/salida -->
      <div
        class="connector connector-input"
        (mouseenter)="showInputLabel = true"
        (mouseleave)="showInputLabel = false"
      >
        <span *ngIf="showInputLabel" class="connector-label">Entrada</span>
      </div>

      <!-- Contenido del nodo -->
      <app-card
        [variant]="getCardVariant()"
        [interactive]="true"
        class="node-content"
      >
        <div class="node-header">
          <div class="node-title">{{ config().title }}</div>
          <div class="node-badge" [ngClass]="'badge-' + getTypeClass()">
            {{ getTypeName() }}
          </div>
        </div>

        <div *ngIf="config().description" class="node-description">
          {{ config().description }}
        </div>

        <div
          *ngIf="config().status"
          class="node-status"
          [ngClass]="'status-' + config().status"
        >
          <span class="status-dot"></span>
          {{ getStatusName() }}
        </div>
      </app-card>

      <!-- Conectores salida -->
      <div
        class="connector connector-output"
        (mouseenter)="showOutputLabel = true"
        (mouseleave)="showOutputLabel = false"
      >
        <span *ngIf="showOutputLabel" class="connector-label">Salida</span>
      </div>

      <!-- Menú acciones -->
      <div class="node-actions" *ngIf="selected()">
        <button
          (click)="delete.emit()"
          class="action-btn delete-btn"
          aria-label="Eliminar nodo"
        >
          🗑️
        </button>
        <button
          (click)="edit.emit()"
          class="action-btn edit-btn"
          aria-label="Editar nodo"
        >
          ✏️
        </button>
      </div>
    </div>
  `,
  styles: [
    `
      .flow-node {
        position: absolute;
        min-width: 200px;
        font-size: 14px;
        user-select: none;
        transition: all 300ms cubic-bezier(0.4, 0, 0.2, 1);

        &.selected {
          .node-content {
            border-color: var(--accent-primary) !important;
            box-shadow: 0 0 0 3px rgba(70, 130, 180, 0.2) !important;
          }
        }

        /* AI Marker */
        .ai-marker {
          position: absolute;
          top: -12px;
          right: 8px;
          background: linear-gradient(135deg, #d69e2e 0%, #c05621 100%);
          border-radius: 20px;
          padding: 2px 8px;
          font-size: 10px;
          font-weight: 600;
          color: #ffffff;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
          z-index: 10;
        }

        .ai-label {
          display: inline-block;
        }

        /* Connectores */
        .connector {
          position: absolute;
          width: 12px;
          height: 12px;
          background: var(--accent-primary);
          border: 2px solid var(--bg-primary);
          border-radius: 50%;
          cursor: crosshair;
          transition: all 200ms ease-out;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

          &:hover {
            width: 16px;
            height: 16px;
            margin: -2px;
            box-shadow: 0 0 8px rgba(70, 130, 180, 0.5);
          }

          &.connector-input {
            left: -6px;
            top: 50%;
            transform: translateY(-50%);
          }

          &.connector-output {
            right: -6px;
            top: 50%;
            transform: translateY(-50%);
          }

          .connector-label {
            position: absolute;
            top: -24px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--bg-secondary);
            color: var(--text-primary);
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            white-space: nowrap;
            border: 1px solid var(--border-light);
            opacity: 0;
            animation: fadeIn 200ms ease-out forwards;
          }

          @keyframes fadeIn {
            to {
              opacity: 1;
            }
          }
        }

        /* Contenido */
        .node-content {
          padding: 12px 16px;
          border: 2px solid var(--border-light);

          .node-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 8px;
            margin-bottom: 8px;
          }

          .node-title {
            font-weight: 700;
            font-size: 14px;
            color: var(--text-primary);
            flex: 1;
            word-break: break-word;
          }

          .node-badge {
            font-size: 10px;
            font-weight: 600;
            padding: 2px 6px;
            border-radius: 3px;
            text-transform: uppercase;
            white-space: nowrap;

            &.badge-start {
              background: var(--state-success);
              color: #ffffff;
            }
            &.badge-step {
              background: var(--accent-secondary);
              color: #ffffff;
            }
            &.badge-decision {
              background: var(--state-warning);
              color: #ffffff;
            }
            &.badge-end {
              background: var(--state-error);
              color: #ffffff;
            }
            &.badge-join,
            &.badge-split {
              background: var(--state-info);
              color: #ffffff;
            }
          }

          .node-description {
            font-size: 12px;
            color: var(--text-secondary);
            margin-bottom: 8px;
            line-height: 1.4;
          }

          .node-status {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 11px;
            font-weight: 500;

            .status-dot {
              width: 6px;
              height: 6px;
              border-radius: 50%;
              display: inline-block;
            }

            &.status-pending {
              color: var(--text-tertiary);
              .status-dot {
                background: #a0aec0;
              }
            }
            &.status-running {
              color: var(--state-info);
              .status-dot {
                background: var(--state-info);
                animation: pulse 1s ease-in-out infinite;
              }
            }
            &.status-completed {
              color: var(--state-success);
              .status-dot {
                background: var(--state-success);
              }
            }
            &.status-failed {
              color: var(--state-error);
              .status-dot {
                background: var(--state-error);
              }
            }
            &.status-skipped {
              color: var(--text-tertiary);
              .status-dot {
                background: #a0aec0;
              }
            }
          }

          @keyframes pulse {
            0%,
            100% {
              opacity: 1;
            }
            50% {
              opacity: 0.5;
            }
          }
        }

        /* Acciones */
        .node-actions {
          position: absolute;
          top: -40px;
          right: 0;
          display: flex;
          gap: 4px;
          background: var(--bg-secondary);
          border: 1px solid var(--border-light);
          border-radius: 6px;
          padding: 4px;
          z-index: 20;
          opacity: 0;
          animation: slideDown 200ms ease-out forwards;

          @keyframes slideDown {
            from {
              transform: translateY(-10px);
              opacity: 0;
            }
            to {
              transform: translateY(0);
              opacity: 1;
            }
          }

          .action-btn {
            padding: 4px 8px;
            border: none;
            background: transparent;
            cursor: pointer;
            font-size: 14px;
            transition: all 200ms ease-out;
            border-radius: 4px;

            &:hover {
              background: var(--bg-tertiary);
            }

            &.delete-btn:hover {
              background: rgba(229, 62, 62, 0.1);
            }

            &.edit-btn:hover {
              background: rgba(70, 130, 180, 0.1);
            }
          }
        }

        /* Dragging state */
        &.dragging {
          opacity: 0.8;
          z-index: 1000;
        }
      }

      /* Responsive */
      @media (max-width: 1024px) {
        .flow-node {
          min-width: 160px;
          font-size: 12px;

          .node-content {
            padding: 10px 12px;
          }
        }
      }
    `,
  ],
})
export class FlowNodeComponent {
  @Input() config!: () => FlowNodeConfig;
  @Input() selected = signal(false);
  @Input() x = signal(0);
  @Input() y = signal(0);

  @Output() select = new EventEmitter<string>();
  @Output() delete = new EventEmitter<string>();
  @Output() edit = new EventEmitter<string>();
  @Output() connect = new EventEmitter<{ from: string; to: string }>();

  showInputLabel = false;
  showOutputLabel = false;
  isDragging = signal(false);

  getCardVariant() {
    if (this.config().aiSuggested) return 'glass';
    if (this.selected()) return 'elevated';
    return 'elevated';
  }

  getTypeClass(): string {
    const typeMap: Record<string, string> = {
      start: 'start',
      step: 'step',
      decision: 'decision',
      end: 'end',
      join: 'join',
      split: 'split',
    };
    return typeMap[this.config().type] || 'step';
  }

  getTypeName(): string {
    const typeNames: Record<string, string> = {
      start: 'Inicio',
      step: 'Paso',
      decision: 'Decisión',
      end: 'Fin',
      join: 'Unir',
      split: 'Dividir',
    };
    return typeNames[this.config().type] || 'Paso';
  }

  getStatusName(): string {
    const statusNames: Record<string, string> = {
      pending: 'Pendiente',
      running: 'En curso',
      completed: 'Completado',
      failed: 'Fallido',
      skipped: 'Omitido',
    };
    return statusNames[this.config().status || ''] || '';
  }

  @HostListener('click')
  onClick(): void {
    this.select.emit(this.config().id);
  }
}
