/**
 * Skeleton Loader Component - Placeholders animados
 *
 * Muestra esqueletos animados mientras se cargan datos,
 * mejorando la percepción de performance.
 */

import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';

type SkeletonType = 'text' | 'card' | 'list' | 'table' | 'avatar';

@Component({
  selector: 'app-skeleton',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div [ngSwitch]="type" class="skeleton">
      <!-- Text Skeleton -->
      <div *ngSwitchCase="'text'" class="skeleton-text">
        <div class="line line-full"></div>
        <div class="line line-full"></div>
        <div class="line line-short"></div>
      </div>

      <!-- Card Skeleton -->
      <div *ngSwitchCase="'card'" class="skeleton-card">
        <div class="card-header">
          <div class="avatar-circle"></div>
          <div class="header-text">
            <div class="line line-title"></div>
            <div class="line line-subtitle"></div>
          </div>
        </div>
        <div class="card-body">
          <div class="line line-full"></div>
          <div class="line line-full"></div>
        </div>
      </div>

      <!-- List Skeleton -->
      <div *ngSwitchCase="'list'" class="skeleton-list">
        <div *ngFor="let i of [0, 1, 2]" class="list-item">
          <div class="avatar-circle"></div>
          <div class="item-text">
            <div class="line line-full"></div>
            <div class="line line-short"></div>
          </div>
        </div>
      </div>

      <!-- Table Skeleton -->
      <div *ngSwitchCase="'table'" class="skeleton-table">
        <div class="table-row header">
          <div class="cell"></div>
          <div class="cell"></div>
          <div class="cell"></div>
        </div>
        <div *ngFor="let i of [0, 1, 2]" class="table-row">
          <div class="cell"></div>
          <div class="cell"></div>
          <div class="cell"></div>
        </div>
      </div>

      <!-- Avatar Skeleton -->
      <div *ngSwitchCase="'avatar'" class="skeleton-avatar">
        <div class="avatar-circle large"></div>
        <div class="avatar-text">
          <div class="line line-title"></div>
          <div class="line line-subtitle"></div>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      .skeleton {
        animation: shimmer 2s infinite;
      }

      /* Base skeleton line */
      .line {
        height: 12px;
        background: linear-gradient(
          90deg,
          var(--bg-tertiary) 25%,
          rgba(255, 255, 255, 0.2) 50%,
          var(--bg-tertiary) 75%
        );
        background-size: 200% 100%;
        border-radius: 4px;
        margin-bottom: 8px;

        &.line-full {
          width: 100%;
        }

        &.line-short {
          width: 60%;
        }

        &.line-title {
          height: 16px;
          width: 80%;
        }

        &.line-subtitle {
          height: 12px;
          width: 60%;
          margin-top: 4px;
        }
      }

      /* Text Skeleton */
      .skeleton-text {
        padding: 16px;
      }

      /* Card Skeleton */
      .skeleton-card {
        padding: 16px;
        background: var(--bg-secondary);
        border-radius: 8px;
        border: 1px solid var(--border-light);

        .card-header {
          display: flex;
          gap: 12px;
          margin-bottom: 16px;

          .avatar-circle {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: var(--bg-tertiary);
            flex-shrink: 0;
          }

          .header-text {
            flex: 1;
          }
        }

        .card-body {
          .line {
            margin-bottom: 8px;
          }
        }
      }

      /* List Skeleton */
      .skeleton-list {
        .list-item {
          display: flex;
          gap: 12px;
          padding: 12px 0;
          border-bottom: 1px solid var(--border-light);

          &:last-child {
            border-bottom: none;
          }

          .avatar-circle {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: var(--bg-tertiary);
            flex-shrink: 0;
          }

          .item-text {
            flex: 1;

            .line {
              margin-bottom: 6px;
              height: 10px;
            }
          }
        }
      }

      /* Table Skeleton */
      .skeleton-table {
        width: 100%;

        .table-row {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 12px;
          padding: 12px;
          border-bottom: 1px solid var(--border-light);

          &.header {
            background: var(--bg-tertiary);
          }

          &:last-child {
            border-bottom: none;
          }

          .cell {
            height: 16px;
            background: var(--bg-tertiary);
            border-radius: 4px;
          }
        }
      }

      /* Avatar Skeleton */
      .skeleton-avatar {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 24px;
        text-align: center;

        .avatar-circle.large {
          width: 80px;
          height: 80px;
          border-radius: 50%;
          background: var(--bg-tertiary);
          margin-bottom: 16px;
        }

        .avatar-text {
          width: 60%;

          .line {
            margin-bottom: 8px;
          }
        }
      }

      @keyframes shimmer {
        0% {
          background-position: -1000px 0;
        }
        100% {
          background-position: 1000px 0;
        }
      }

      /* Accesibilidad - Respetar preferencias de movimiento reducido */
      @media (prefers-reduced-motion: reduce) {
        .skeleton {
          animation: none;
          background-color: var(--bg-tertiary);
        }
      }
    `,
  ],
})
export class SkeletonComponent {
  @Input() type: SkeletonType = 'text';
}
