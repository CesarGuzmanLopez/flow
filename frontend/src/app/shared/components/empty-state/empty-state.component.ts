/**
 * Empty State Component - Estados vacíos empáticos
 *
 * Muestra mensajes motivadores con ilustraciones animadas
 * cuando no hay datos disponibles.
 */

import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';

type EmptyStateType = 'no-data' | 'error' | 'no-results' | 'loading';

@Component({
  selector: 'app-empty-state',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="empty-state" [class]="'empty-state-' + type">
      <div class="illustration">
        <div [ngSwitch]="type" class="icon-wrapper">
          <!-- No Data -->
          <div *ngSwitchCase="'no-data'" class="icon icon-inbox">
            <div class="inbox-item item-1"></div>
            <div class="inbox-item item-2"></div>
            <div class="inbox-line"></div>
          </div>

          <!-- Error -->
          <div *ngSwitchCase="'error'" class="icon icon-error">
            <div class="error-circle">
              <div class="error-x"></div>
            </div>
          </div>

          <!-- No Results -->
          <div *ngSwitchCase="'no-results'" class="icon icon-search">
            <div class="search-circle"></div>
            <div class="search-line"></div>
          </div>

          <!-- Loading -->
          <div *ngSwitchCase="'loading'" class="icon icon-loading">
            <div class="spinner"></div>
          </div>
        </div>
      </div>

      <h3 class="title">{{ title }}</h3>
      <p class="message">{{ message }}</p>

      <button *ngIf="buttonLabel" (click)="handleAction()" class="action-btn">
        {{ buttonLabel }}
      </button>
    </div>
  `,
  styles: [
    `
      .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 60px 24px;
        text-align: center;
        background: var(--bg-primary);
        border-radius: 8px;
        min-height: 400px;

        .illustration {
          margin-bottom: 24px;
        }

        .icon-wrapper {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 120px;
          height: 120px;
          margin: 0 auto;
          position: relative;
        }

        .icon {
          width: 100%;
          height: 100%;
          position: relative;

          /* Inbox Icon */
          &.icon-inbox {
            .inbox-item {
              position: absolute;
              background: var(--accent-secondary);
              border-radius: 4px;
              animation: slideInUp 500ms ease-out forwards;

              &.item-1 {
                width: 60px;
                height: 40px;
                top: 20px;
                left: 20px;
                animation-delay: 100ms;
              }

              &.item-2 {
                width: 50px;
                height: 35px;
                bottom: 30px;
                right: 15px;
                animation-delay: 200ms;
              }
            }

            .inbox-line {
              position: absolute;
              width: 2px;
              height: 40px;
              background: var(--accent-primary);
              bottom: 20px;
              left: 50%;
              transform: translateX(-50%);
              opacity: 0.3;
              animation: slideInUp 600ms ease-out forwards;
              animation-delay: 300ms;
            }
          }

          /* Error Icon */
          &.icon-error {
            .error-circle {
              width: 100%;
              height: 100%;
              border: 4px solid var(--state-error);
              border-radius: 50%;
              position: relative;
              animation: pulse 2s ease-in-out infinite;

              .error-x {
                position: absolute;
                width: 60%;
                height: 60%;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);

                &::before,
                &::after {
                  content: '';
                  position: absolute;
                  background: var(--state-error);
                  animation: rotateX 400ms ease-out forwards;
                  animation-delay: 200ms;
                }

                &::before {
                  width: 4px;
                  height: 70%;
                  top: 15%;
                  left: 50%;
                  transform: translateX(-50%) rotate(45deg);
                }

                &::after {
                  width: 4px;
                  height: 70%;
                  top: 15%;
                  left: 50%;
                  transform: translateX(-50%) rotate(-45deg);
                }
              }
            }
          }

          /* Search Icon */
          &.icon-search {
            .search-circle {
              width: 70%;
              height: 70%;
              border: 3px solid var(--accent-primary);
              border-radius: 50%;
              animation: slideInLeft 500ms ease-out forwards;
            }

            .search-line {
              position: absolute;
              width: 3px;
              height: 40%;
              background: var(--accent-primary);
              bottom: 0;
              right: 5%;
              transform: rotate(-45deg);
              transform-origin: top center;
              animation: slideInRight 500ms ease-out forwards;
              animation-delay: 200ms;
            }
          }

          /* Loading Icon */
          &.icon-loading {
            .spinner {
              width: 80%;
              height: 80%;
              border: 3px solid var(--border-light);
              border-top-color: var(--accent-primary);
              border-radius: 50%;
              animation: spin 1s linear infinite;
            }
          }
        }

        .title {
          font-size: 20px;
          font-weight: 700;
          color: var(--text-primary);
          margin-bottom: 8px;
        }

        .message {
          font-size: 14px;
          color: var(--text-secondary);
          margin-bottom: 24px;
          max-width: 400px;
          line-height: 1.6;
        }

        .action-btn {
          margin-top: 8px;
        }
      }

      @keyframes slideInUp {
        from {
          transform: translateY(20px);
          opacity: 0;
        }
        to {
          transform: translateY(0);
          opacity: 1;
        }
      }

      @keyframes slideInLeft {
        from {
          transform: translateX(-20px);
          opacity: 0;
        }
        to {
          transform: translateX(0);
          opacity: 1;
        }
      }

      @keyframes slideInRight {
        from {
          transform: translateX(20px);
          opacity: 0;
        }
        to {
          transform: translateX(0);
          opacity: 1;
        }
      }

      @keyframes spin {
        to {
          transform: rotate(360deg);
        }
      }

      @keyframes pulse {
        0%,
        100% {
          box-shadow: 0 0 0 0 rgba(229, 62, 62, 0.7);
        }
        50% {
          box-shadow: 0 0 0 10px rgba(229, 62, 62, 0);
        }
      }

      @keyframes rotateX {
        from {
          opacity: 0;
          transform: rotate(0deg);
        }
        to {
          opacity: 1;
          transform: rotate(90deg);
        }
      }

      /* Responsive */
      @media (max-width: 600px) {
        .empty-state {
          padding: 40px 16px;
          min-height: 300px;

          .icon-wrapper {
            width: 80px;
            height: 80px;
          }

          .title {
            font-size: 16px;
          }

          .message {
            font-size: 13px;
          }
        }
      }
    `,
  ],
})
export class EmptyStateComponent {
  @Input() type: EmptyStateType = 'no-data';
  @Input() title = '¡Sin datos!';
  @Input() message = 'No hay nada que mostrar aquí.';
  @Input() buttonLabel?: string;
  @Output() action = new EventEmitter<void>();

  handleAction(): void {
    this.action.emit();
  }
}
