/**
 * Theme Provider - Sistema centralizado de temas
 *
 * Maneja transición entre modo claro y oscuro,
 * almacena preferencias y aplica cambios dinámicamente.
 */

import { Injectable, effect, signal } from '@angular/core';
import { DesignTokens, ThemeMode } from './design-tokens';

@Injectable({
  providedIn: 'root',
})
export class ThemeService {
  // Signal reactivo para el modo actual
  private themeMode = signal<ThemeMode>(this.getSystemTheme());

  // Observable público
  themeMode$ = this.themeMode.asReadonly();

  constructor() {
    // Aplicar tema al iniciar
    this.applyTheme(this.themeMode());

    // Effect para aplicar cambios automáticamente
    effect(() => {
      this.applyTheme(this.themeMode());
      localStorage.setItem('theme-mode', this.themeMode());
    });

    // Escuchar cambios en preferencias del sistema
    this.watchSystemPreferences();
  }

  /**
   * Obtener tema preferido del sistema
   */
  private getSystemTheme(): ThemeMode {
    // Intentar cargar preferencia guardada
    const saved = localStorage.getItem('theme-mode') as ThemeMode | null;
    if (saved === 'light' || saved === 'dark') {
      return saved;
    }

    // Fallback a preferencia del sistema
    if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }
    return 'light';
  }

  /**
   * Alternar entre temas
   */
  toggleTheme(): void {
    this.themeMode.set(this.themeMode() === 'light' ? 'dark' : 'light');
  }

  /**
   * Establecer tema explícitamente
   */
  setTheme(mode: ThemeMode): void {
    this.themeMode.set(mode);
  }

  /**
   * Obtener modo actual
   */
  getCurrentTheme(): ThemeMode {
    return this.themeMode();
  }

  /**
   * Obtener colores para el tema actual
   */
  getColors() {
    return DesignTokens.colors[this.themeMode()];
  }

  /**
   * Aplicar tema al documento
   */
  private applyTheme(mode: ThemeMode): void {
    const root = document.documentElement;
    const colors = DesignTokens.colors[mode];

    // Aplicar variables CSS
    root.style.setProperty('--theme-mode', mode);
    root.style.setProperty('--bg-primary', colors.background.primary);
    root.style.setProperty('--bg-secondary', colors.background.secondary);
    root.style.setProperty('--bg-tertiary', colors.background.tertiary);
    root.style.setProperty('--text-primary', colors.text.primary);
    root.style.setProperty('--text-secondary', colors.text.secondary);
    root.style.setProperty('--accent-primary', colors.accent.primary);
    root.style.setProperty('--accent-secondary', colors.accent.secondary);
    root.style.setProperty('--state-success', colors.state.success);
    root.style.setProperty('--state-error', colors.state.error);
    root.style.setProperty('--state-warning', colors.state.warning);
    root.style.setProperty('--border-light', colors.border.light);
    root.style.setProperty('--border-dark', colors.border.dark);

    // Aplicar atributo data para selectores CSS
    root.setAttribute('data-theme', mode);
  }

  /**
   * Escuchar cambios en las preferencias del sistema
   */
  private watchSystemPreferences(): void {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    mediaQuery.addEventListener('change', (e) => {
      // Solo actualizar si el usuario no ha establecido una preferencia explícita
      const saved = localStorage.getItem('theme-mode');
      if (!saved) {
        this.themeMode.set(e.matches ? 'dark' : 'light');
      }
    });
  }
}
