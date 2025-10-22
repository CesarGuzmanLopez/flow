/**
 * Button Component - Sistema de botones reutilizable
 *
 * Soporta múltiples variantes, tamaños y estados.
 * Integra accesibilidad WCAG AA.
 */

import { CommonModule } from '@angular/common';
import {
  Component,
  EventEmitter,
  HostBinding,
  Input,
  Output,
} from '@angular/core';

type ButtonVariant =
  | 'primary'
  | 'secondary'
  | 'tertiary'
  | 'danger'
  | 'success'
  | 'ghost';
type ButtonSize = 'sm' | 'md' | 'lg';
type ButtonType = 'button' | 'submit' | 'reset';

@Component({
  selector: 'app-button',
  standalone: true,
  imports: [CommonModule],
  template: `
    <button
      [type]="type"
      [disabled]="disabled || loading"
      [attr.aria-label]="ariaLabel"
      [attr.aria-busy]="loading"
      class="app-button"
    >
      <span class="button-content">
        <span *ngIf="loading" class="spinner"></span>
        <ng-content></ng-content>
      </span>
    </button>
  `,
  styles: [
    `
      .app-button {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        font-family: inherit;
        font-weight: 600;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        transition: all 300ms cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;

        /* Tamaños */
        padding: 8px 16px;
        font-size: 14px;

        &.size-sm {
          padding: 6px 12px;
          font-size: 12px;
        }

        &.size-lg {
          padding: 12px 24px;
          font-size: 16px;
        }

        /* Variantes - Modo Claro */
        &.variant-primary {
          background: linear-gradient(135deg, #4682b4 0%, #2b6cb0 100%);
          color: #ffffff;
          box-shadow: 0 2px 8px rgba(70, 130, 180, 0.3);

          &:hover:not(:disabled) {
            background: linear-gradient(135deg, #3a7ba8 0%, #2456a3 100%);
            box-shadow: 0 4px 12px rgba(70, 130, 180, 0.4);
            transform: translateY(-2px);
          }

          &:active:not(:disabled) {
            transform: translateY(0);
          }
        }

        &.variant-secondary {
          background: var(--bg-secondary);
          color: var(--text-primary);
          border: 1px solid var(--border-light);

          &:hover:not(:disabled) {
            background: var(--bg-tertiary);
            border-color: var(--border-medium);
          }
        }

        &.variant-tertiary {
          background: transparent;
          color: var(--accent-primary);
          border: 1px solid var(--accent-primary);

          &:hover:not(:disabled) {
            background: rgba(70, 130, 180, 0.1);
          }
        }

        &.variant-danger {
          background: var(--state-error);
          color: #ffffff;

          &:hover:not(:disabled) {
            background: #d32f2f;
          }
        }

        &.variant-success {
          background: var(--state-success);
          color: #ffffff;

          &:hover:not(:disabled) {
            background: #2d7a34;
          }
        }

        &.variant-ghost {
          background: transparent;
          color: var(--text-primary);

          &:hover:not(:disabled) {
            background: var(--bg-secondary);
          }
        }

        /* Estados */
        &:focus-visible {
          outline: 2px solid var(--accent-primary);
          outline-offset: 2px;
        }

        &:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .button-content {
          display: inline-flex;
          align-items: center;
          gap: 8px;
        }

        /* Loading spinner */
        .spinner {
          width: 16px;
          height: 16px;
          border: 2px solid rgba(255, 255, 255, 0.3);
          border-top-color: currentColor;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }
      }

      /* Modo oscuro */
      :root[data-theme='dark'] .app-button {
        &.variant-primary {
          background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
          color: #121212;
          box-shadow: 0 2px 8px rgba(60, 165, 250, 0.4);

          &:hover:not(:disabled) {
            background: linear-gradient(135deg, #93c5fd 0%, #60a5fa 100%);
            box-shadow: 0 4px 12px rgba(60, 165, 250, 0.5);
          }
        }

        &.variant-secondary {
          background: var(--bg-secondary);
          border-color: var(--border-dark);

          &:hover:not(:disabled) {
            background: var(--bg-tertiary);
          }
        }
      }
    `,
  ],
})
export class ButtonComponent {
  @Input() variant: ButtonVariant = 'primary';
  @Input() size: ButtonSize = 'md';
  @Input() type: ButtonType = 'button';
  @Input() disabled = false;
  @Input() loading = false;
  @Input() ariaLabel?: string;

  @Output() click = new EventEmitter<void>();

  @HostBinding('class.app-button') hostClass = true;
  @HostBinding('class') get buttonClass(): string {
    return `variant-${this.variant} size-${this.size}`;
  }

  onClick(): void {
    if (!this.disabled && !this.loading) {
      this.click.emit();
    }
  }
}
