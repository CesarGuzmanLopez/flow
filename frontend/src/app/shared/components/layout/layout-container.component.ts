/**
 * Responsive Layout Container
 *
 * Sistema de layout responsive con sidebars colapsables,
 * soporte mobile-first y breakpoints modernos.
 */

import { CommonModule } from '@angular/common';
import { Component, Input, signal } from '@angular/core';

type SidebarPosition = 'left' | 'right' | 'both';

@Component({
  selector: 'app-layout-container',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="layout-container" [class]="'sidebar-' + sidebarPosition">
      <!-- Mobile Header -->
      <header class="mobile-header" *ngIf="isMobile()">
        <button
          (click)="toggleLeftSidebar()"
          class="sidebar-toggle left-toggle"
          *ngIf="hasLeftSidebar"
        >
          ☰
        </button>
        <div class="header-title">{{ title }}</div>
        <button
          (click)="toggleRightSidebar()"
          class="sidebar-toggle right-toggle"
          *ngIf="hasRightSidebar"
        >
          ⋮
        </button>
      </header>

      <!-- Left Sidebar -->
      <aside
        class="sidebar sidebar-left"
        [class.collapsed]="!leftSidebarOpen()"
        [class.mobile]="isMobile()"
        *ngIf="hasLeftSidebar"
      >
        <ng-content select="[sidebar-left]"></ng-content>
      </aside>

      <!-- Main Content -->
      <main class="main-content">
        <ng-content select="[main-content]"></ng-content>
      </main>

      <!-- Right Sidebar -->
      <aside
        class="sidebar sidebar-right"
        [class.collapsed]="!rightSidebarOpen()"
        [class.mobile]="isMobile()"
        *ngIf="hasRightSidebar"
      >
        <ng-content select="[sidebar-right]"></ng-content>
      </aside>

      <!-- Mobile Backdrop -->
      <div
        class="mobile-backdrop"
        *ngIf="isMobile() && (leftSidebarOpen() || rightSidebarOpen())"
        (click)="closeSidebars()"
      ></div>
    </div>
  `,
  styles: [
    `
      .layout-container {
        display: grid;
        grid-template-columns: auto 1fr auto;
        grid-template-rows: auto 1fr;
        height: 100vh;
        background: var(--bg-primary);
        overflow: hidden;

        /* Diferentes configuraciones de sidebars */
        &.sidebar-left {
          grid-template-columns: 240px 1fr auto;
        }

        &.sidebar-right {
          grid-template-columns: auto 1fr 300px;
        }

        &.sidebar-both {
          grid-template-columns: 240px 1fr 300px;
        }
      }

      /* Mobile Header */
      .mobile-header {
        display: none;
        grid-column: 1 / -1;
        align-items: center;
        justify-content: space-between;
        padding: 12px 16px;
        background: var(--bg-secondary);
        border-bottom: 1px solid var(--border-light);
        height: 56px;
        z-index: 100;

        .header-title {
          font-size: 16px;
          font-weight: 600;
          color: var(--text-primary);
          flex: 1;
          text-align: center;
        }

        .sidebar-toggle {
          background: none;
          border: none;
          color: var(--text-primary);
          font-size: 20px;
          padding: 8px;
          cursor: pointer;
          transition: color 200ms ease-out;

          &:hover {
            color: var(--accent-primary);
          }
        }
      }

      /* Sidebars */
      .sidebar {
        background: var(--bg-secondary);
        border: 1px solid var(--border-light);
        overflow-y: auto;
        transition: all 300ms cubic-bezier(0.4, 0, 0.2, 1);
        z-index: 50;

        /* Desktop */
        &:not(.mobile) {
          padding: 16px;

          &.sidebar-left {
            grid-column: 1;
            grid-row: 1 / -1;
            border-right-width: 1px;
            border-bottom-width: 0;
          }

          &.sidebar-right {
            grid-column: 3;
            grid-row: 1 / -1;
            border-left-width: 1px;
            border-bottom-width: 0;
          }

          &.collapsed {
            width: 64px;
            padding: 12px;

            /* Ocultar texto en versión colapsada */
            :deep(.sidebar-title),
            :deep(.sidebar-label) {
              display: none;
            }

            /* Mostrar solo iconos */
            :deep(.sidebar-icon) {
              margin: 0 auto;
            }
          }
        }

        /* Mobile */
        &.mobile {
          position: fixed;
          top: 56px;
          height: calc(100vh - 56px);
          width: 100%;
          max-width: 280px;
          padding: 16px;
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);

          &.sidebar-left {
            left: 0;
            transform: translateX(-100%);
            border-right-width: 1px;
            border-bottom-width: 0;
          }

          &.sidebar-right {
            right: 0;
            transform: translateX(100%);
            border-left-width: 1px;
            border-bottom-width: 0;
          }

          &:not(.collapsed) {
            transform: translateX(0);
          }
        }
      }

      /* Main Content */
      .main-content {
        grid-column: 2;
        grid-row: 1 / -1;
        overflow-y: auto;
        padding: 16px;

        @media (max-width: 1024px) {
          padding: 12px;
        }

        @media (max-width: 600px) {
          grid-column: 1 / -1;
          grid-row: 2;
          padding: 12px;
        }
      }

      /* Mobile Backdrop */
      .mobile-backdrop {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.4);
        z-index: 40;
        animation: fadeIn 200ms ease-out;
      }

      @keyframes fadeIn {
        from {
          opacity: 0;
        }
        to {
          opacity: 1;
        }
      }

      /* Responsive Breakpoints */
      @media (max-width: 1440px) {
        .layout-container {
          &.sidebar-left {
            grid-template-columns: 200px 1fr auto;
          }

          &.sidebar-right {
            grid-template-columns: auto 1fr 280px;
          }

          &.sidebar-both {
            grid-template-columns: 200px 1fr 280px;
          }
        }
      }

      @media (max-width: 1024px) {
        .layout-container {
          grid-template-columns: 1fr;

          .sidebar:not(.mobile) {
            display: none;
          }
        }
      }

      @media (max-width: 600px) {
        .layout-container {
          grid-template-rows: 56px 1fr;
          height: 100%;
        }

        .mobile-header {
          display: flex;
        }

        .main-content {
          grid-column: 1 / -1;
        }

        .sidebar {
          max-width: 100%;

          &.mobile {
            top: 56px;
            height: calc(100% - 56px);
          }
        }
      }

      /* Scroll personalizado para sidebars */
      .sidebar::-webkit-scrollbar {
        width: 6px;
      }

      .sidebar::-webkit-scrollbar-track {
        background: var(--bg-primary);
      }

      .sidebar::-webkit-scrollbar-thumb {
        background: var(--border-medium);
        border-radius: 3px;

        &:hover {
          background: var(--border-dark);
        }
      }
    `,
  ],
})
export class LayoutContainerComponent {
  @Input() title = 'ChemFlow';
  @Input() sidebarPosition: SidebarPosition = 'both';
  @Input() hasLeftSidebar = true;
  @Input() hasRightSidebar = true;

  leftSidebarOpen = signal(true);
  rightSidebarOpen = signal(true);
  isMobile = signal(false);

  ngOnInit() {
    // Detectar cambios en viewport
    this.checkMobile();
    window.addEventListener('resize', () => this.checkMobile());
  }

  private checkMobile(): void {
    const isMobile = window.innerWidth <= 1024;
    this.isMobile.set(isMobile);

    // Cerrar sidebars en mobile por defecto
    if (isMobile) {
      this.leftSidebarOpen.set(false);
      this.rightSidebarOpen.set(false);
    }
  }

  toggleLeftSidebar(): void {
    this.leftSidebarOpen.update((v) => !v);
  }

  toggleRightSidebar(): void {
    this.rightSidebarOpen.update((v) => !v);
  }

  closeSidebars(): void {
    this.leftSidebarOpen.set(false);
    this.rightSidebarOpen.set(false);
  }
}
