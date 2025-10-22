/**
 * Card Component - Contenedor visual reutilizable
 *
 * Implementa neumorfismo y glassmorphism.
 * Base para nodos en diagramas y paneles.
 */

import { CommonModule } from '@angular/common';
import { Component, HostBinding, Input } from '@angular/core';

type CardVariant = 'elevated' | 'outlined' | 'filled' | 'glass';
type CardSize = 'sm' | 'md' | 'lg';

@Component({
  selector: 'app-card',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="app-card" [attr.role]="interactive ? 'button' : 'region'">
      <ng-content></ng-content>
    </div>
  `,
  styles: [
    `
      .app-card {
        background: var(--bg-secondary);
        border-radius: 8px;
        padding: 16px;
        transition: all 300ms cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid var(--border-light);

        /* Variantes */
        &.variant-elevated {
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

          &:hover {
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
            transform: translateY(-2px);
          }
        }

        &.variant-outlined {
          border: 2px solid var(--border-medium);
          background: transparent;
        }

        &.variant-filled {
          background: var(--bg-tertiary);
          border: none;
        }

        &.variant-glass {
          background: rgba(255, 255, 255, 0.7);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.5);
          box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
        }

        /* Tamaños */
        &.size-sm {
          padding: 12px;
        }

        &.size-lg {
          padding: 24px;
        }

        /* Interactive */
        &.interactive {
          cursor: pointer;

          &:hover {
            border-color: var(--accent-primary);
          }

          &:focus-within {
            outline: 2px solid var(--accent-primary);
            outline-offset: 2px;
          }
        }

        /* Modo oscuro */
        @media (prefers-color-scheme: dark) {
          &.variant-glass {
            background: rgba(30, 30, 30, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.1);
          }
        }
      }
    `,
  ],
})
export class CardComponent {
  @Input() variant: CardVariant = 'elevated';
  @Input() size: CardSize = 'md';
  @Input() interactive = false;

  @HostBinding('class.app-card') hostClass = true;
  @HostBinding('class') get cardClass(): string {
    const classes = [`variant-${this.variant}`, `size-${this.size}`];
    if (this.interactive) classes.push('interactive');
    return classes.join(' ');
  }
}
