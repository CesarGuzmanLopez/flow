/**
 * Design Tokens para ChemFlow
 *
 * Sistema centralizado de tokens de diseño siguiendo tendencias modernas:
 * - Paleta de colores con modo claro/oscuro
 * - Espaciado modular
 * - Tipografía escalable
 * - Sombras y elevaciones
 * - Transiciones y animaciones
 * - Radios y otros valores
 */

export const DesignTokens = {
  // ============================================
  // COLOR PALETTE - Modo Claro y Oscuro
  // ============================================
  colors: {
    light: {
      // Fondos - Paleta terrosa y cálida
      background: {
        primary: '#FFFFFF', // Canvas principal
        secondary: '#F7FAFC', // Paneles secundarios
        tertiary: '#EDF2F7', // Áreas deshabilitadas
        elevated: '#FAFBFC', // Elementos elevados
        overlay: 'rgba(255, 255, 255, 0.95)', // Overlays
      },
      // Superficies - Neumorfismo
      surface: {
        base: '#FFFFFF',
        hover: '#F0F4F8',
        active: '#E2E8F0',
        disabled: '#F7FAFC',
      },
      // Texto - Contraste WCAG AA
      text: {
        primary: '#1A202C', // Títulos y contenido principal
        secondary: '#4A5568', // Subtítulos y descripciones
        tertiary: '#718096', // Hints y texto muted
        inverse: '#FFFFFF', // Texto en fondos oscuros
      },
      // Acentos - Azules serenos y vibrantes
      accent: {
        primary: '#4682B4', // Azul sereno para CTA
        secondary: '#2B6CB0', // Azul más oscuro
        tertiary: '#6DA3D7', // Azul más claro
        hover: '#3A7BA8',
        active: '#2C5FB0',
      },
      // Estados
      state: {
        success: '#38A169', // Verde
        warning: '#D69E2E', // Naranja
        error: '#E53E3E', // Rojo
        info: '#3182CE', // Azul claro
      },
      // Gradientes
      gradient: {
        primary: 'linear-gradient(135deg, #4682B4 0%, #2B6CB0 100%)',
        accent: 'linear-gradient(135deg, #ECE9E6 0%, #FFFFFF 100%)',
        warning: 'linear-gradient(135deg, #D69E2E 0%, #C05621 100%)',
        success: 'linear-gradient(135deg, #38A169 0%, #22543D 100%)',
      },
      // Bordes
      border: {
        light: '#E2E8F0',
        medium: '#CBD5E0',
        dark: '#A0AEC0',
      },
    },
    dark: {
      // Fondos - Oscuros y nocturnos
      background: {
        primary: '#121212', // Canvas principal
        secondary: '#1E1E1E', // Paneles secundarios
        tertiary: '#2D2D2D', // Áreas deshabilitadas
        elevated: '#242424', // Elementos elevados
        overlay: 'rgba(18, 18, 18, 0.95)',
      },
      // Superficies
      surface: {
        base: '#1E1E1E',
        hover: '#2D2D2D',
        active: '#3D3D3D',
        disabled: '#121212',
      },
      // Texto - Alto contraste
      text: {
        primary: '#F7FAFC',
        secondary: '#CBD5E0',
        tertiary: '#A0AEC0',
        inverse: '#121212',
      },
      // Acentos - Neon y vibrante
      accent: {
        primary: '#60A5FA', // Azul neon
        secondary: '#93C5FD', // Azul más claro
        tertiary: '#3B82F6', // Azul vibrante
        hover: '#BFDBFE',
        active: '#60A5FA',
      },
      // Estados
      state: {
        success: '#4ADE80', // Verde neon
        warning: '#FBBF24', // Naranja neon
        error: '#F87171', // Rojo neon
        info: '#38BDF8', // Cian neon
      },
      // Gradientes
      gradient: {
        primary: 'linear-gradient(135deg, #60A5FA 0%, #3B82F6 100%)',
        accent: 'linear-gradient(135deg, #1F2937 0%, #111827 100%)',
        warning: 'linear-gradient(135deg, #FBBF24 0%, #F59E0B 100%)',
        success: 'linear-gradient(135deg, #4ADE80 0%, #16A34A 100%)',
      },
      // Bordes
      border: {
        light: '#3D3D3D',
        medium: '#4D4D4D',
        dark: '#5D5D5D',
      },
    },
  },

  // ============================================
  // SPACING - Sistema modular
  // ============================================
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    xxl: '48px',
    // Aliases para Canvas/Diagramas
    canvas: {
      gapSmall: '40px', // Espacio entre nodos pequeños
      gapMedium: '60px', // Espacio estándar entre nodos
      gapLarge: '100px', // Espacio entre ramas principales
    },
  },

  // ============================================
  // TYPOGRAPHY - Bold y dinámica
  // ============================================
  typography: {
    // Headings - Bold y grandes
    heading: {
      h1: {
        fontSize: '32px',
        fontWeight: 700,
        lineHeight: '1.2',
        letterSpacing: '-0.5px',
      },
      h2: {
        fontSize: '24px',
        fontWeight: 700,
        lineHeight: '1.3',
        letterSpacing: '-0.25px',
      },
      h3: {
        fontSize: '20px',
        fontWeight: 700,
        lineHeight: '1.4',
      },
      h4: {
        fontSize: '16px',
        fontWeight: 700,
        lineHeight: '1.5',
      },
    },
    // Body - Legible y escalable
    body: {
      large: {
        fontSize: '16px',
        fontWeight: 500,
        lineHeight: '1.6',
      },
      regular: {
        fontSize: '14px',
        fontWeight: 400,
        lineHeight: '1.6',
      },
      small: {
        fontSize: '12px',
        fontWeight: 400,
        lineHeight: '1.5',
      },
    },
    // Labels y etiquetas
    label: {
      large: {
        fontSize: '14px',
        fontWeight: 600,
        lineHeight: '1.5',
        textTransform: 'none',
      },
      regular: {
        fontSize: '12px',
        fontWeight: 600,
        lineHeight: '1.5',
      },
    },
    // Mono para código
    mono: {
      fontSize: '13px',
      fontWeight: 400,
      fontFamily: "'Roboto Mono', monospace",
      lineHeight: '1.6',
    },
  },

  // ============================================
  // SHADOWS y ELEVACIONES - Neumorfismo
  // ============================================
  shadow: {
    // Sombras neumórficas (modo claro)
    light: {
      sm: '2px 2px 5px rgba(0, 0, 0, 0.08), -2px -2px 5px rgba(255, 255, 255, 0.8)',
      md: '5px 5px 10px rgba(0, 0, 0, 0.1), -5px -5px 10px rgba(255, 255, 255, 0.9)',
      lg: '8px 8px 16px rgba(0, 0, 0, 0.12), -8px -8px 16px rgba(255, 255, 255, 0.95)',
      xl: '12px 12px 24px rgba(0, 0, 0, 0.15), -12px -12px 24px rgba(255, 255, 255, 0.98)',
    },
    // Sombras para modo oscuro
    dark: {
      sm: '2px 2px 5px rgba(0, 0, 0, 0.5)',
      md: '5px 5px 10px rgba(0, 0, 0, 0.6)',
      lg: '8px 8px 16px rgba(0, 0, 0, 0.7)',
      xl: '12px 12px 24px rgba(0, 0, 0, 0.8)',
    },
    // Sombras estándar
    standard: {
      sm: '0 2px 4px rgba(0, 0, 0, 0.1)',
      md: '0 4px 8px rgba(0, 0, 0, 0.12)',
      lg: '0 8px 16px rgba(0, 0, 0, 0.15)',
      xl: '0 12px 24px rgba(0, 0, 0, 0.2)',
    },
  },

  // ============================================
  // BORDER RADIUS
  // ============================================
  radius: {
    xs: '2px',
    sm: '4px',
    md: '6px',
    lg: '8px',
    xl: '12px',
    full: '9999px',
    // Específico para nodos
    node: '8px',
    card: '8px',
  },

  // ============================================
  // TRANSICIONES y ANIMACIONES
  // ============================================
  transition: {
    // Duraciones estándar
    fast: '150ms',
    base: '300ms',
    slow: '500ms',
    // Easing functions
    easing: {
      easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
      easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
      easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
      easeOutBack: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
    },
  },

  // ============================================
  // BREAKPOINTS - Responsive
  // ============================================
  breakpoints: {
    xs: '0px', // Mobile
    sm: '600px', // Tablet small
    md: '1024px', // Tablet large
    lg: '1440px', // Desktop
    xl: '1920px', // Large desktop
  },

  // ============================================
  // Z-INDEX SCALE
  // ============================================
  zIndex: {
    hide: -1,
    base: 0,
    dropdown: 1000,
    sticky: 1050,
    fixed: 1060,
    modal: 1070,
    popover: 1080,
    tooltip: 1090,
  },

  // ============================================
  // STATES - Interactive
  // ============================================
  state: {
    // Opcacidades
    opacity: {
      disabled: 0.5,
      hover: 0.85,
      focus: 0.95,
      active: 1,
    },
    // Transiciones por estado
    transition: 'all 300ms cubic-bezier(0.4, 0, 0.2, 1)',
  },
};

export type ThemeMode = 'light' | 'dark';

/**
 * Helper para obtener colores según el modo
 */
export function getColorsByTheme(mode: ThemeMode) {
  return DesignTokens.colors[mode];
}
