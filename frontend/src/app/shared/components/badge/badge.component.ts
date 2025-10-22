/**
 * Badge Component - Etiquetas de estado
 *
 * Muestra etiquetas con diferentes variantes y estados.
 */

import { CommonModule } from '@angular/common';
import { Component, HostBinding, Input } from '@angular/core';

type BadgeVariant =
  | 'primary'
  | 'secondary'
  | 'success'
  | 'warning'
  | 'error'
  | 'info';
type BadgeSize = 'sm' | 'md' | 'lg';

@Component({
  selector: 'app-badge',
  standalone: true,
  imports: [CommonModule],
  template: `<span class="badge"><ng-content></ng-content></span>`,
  styles: [
    `
      .badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        white-space: nowrap;
        transition: all 300ms cubic-bezier(0.4, 0, 0.2, 1);

        /* Variantes */
        &.variant-primary {
          background: linear-gradient(135deg, #4682b4 0%, #2b6cb0 100%);
          color: #ffffff;
        }

        &.variant-secondary {
          background: var(--bg-tertiary);
          color: var(--text-primary);
          border: 1px solid var(--border-light);
        }

        &.variant-success {
          background: rgba(56, 161, 105, 0.1);
          color: var(--state-success);
          border: 1px solid var(--state-success);
        }

        &.variant-warning {
          background: rgba(214, 158, 46, 0.1);
          color: var(--state-warning);
          border: 1px solid var(--state-warning);
        }

        &.variant-error {
          background: rgba(229, 62, 62, 0.1);
          color: var(--state-error);
          border: 1px solid var(--state-error);
        }

        &.variant-info {
          background: rgba(49, 130, 206, 0.1);
          color: var(--state-info);
          border: 1px solid var(--state-info);
        }

        /* Tamaños */
        &.size-sm {
          padding: 2px 6px;
          font-size: 10px;
        }

        &.size-lg {
          padding: 6px 12px;
          font-size: 12px;
        }

        /* Dot de estado */
        &.with-dot {
          position: relative;
          padding-left: 16px;

          &::before {
            content: '';
            position: absolute;
            left: 6px;
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: currentColor;
            animation: pulse 2s ease-in-out infinite;
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

      /* Modo oscuro */
      :root[data-theme='dark'] .badge {
        &.variant-primary {
          background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
          color: #121212;
        }

        &.variant-secondary {
          background: var(--bg-tertiary);
          border-color: var(--border-dark);
        }
      }
    `,
  ],
})
export class BadgeComponent {
  @Input() variant: BadgeVariant = 'primary';
  @Input() size: BadgeSize = 'md';
  @Input() withDot = false;

  @HostBinding('class.badge') hostClass = true;
  @HostBinding('class') get badgeClass(): string {
    const classes = [`variant-${this.variant}`, `size-${this.size}`];
    if (this.withDot) classes.push('with-dot');
    return classes.join(' ');
  }
}
