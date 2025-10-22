/**
 * AI Recommendation Service
 *
 * Proporciona sugerencias inteligentes basadas en:
 * - Historial de flujos del usuario
 * - Patrones comunes observados
 * - Contexto del flujo actual
 * - Mejor prácticas del dominio
 */

import { HttpClient } from '@angular/common/http';
import { Injectable, signal } from '@angular/core';
import { Observable, of } from 'rxjs';
import { catchError } from 'rxjs/operators';

export interface NodeSuggestion {
  id: string;
  type: 'start' | 'step' | 'decision' | 'end' | 'join' | 'split';
  title: string;
  description?: string;
  confidence: number; // 0-1
  reason: string;
  aiGenerated: boolean;
}

export interface FlowPattern {
  id: string;
  name: string;
  description: string;
  nodeSequence: string[]; // IDs de tipos de nodos
  frequency: number;
  domain: string;
}

@Injectable({
  providedIn: 'root',
})
export class AIRecommendationService {
  private apiUrl = '/api/flows/recommendations';

  // Patrones predefinidos comunes
  private commonPatterns: FlowPattern[] = [
    {
      id: 'pattern-1',
      name: 'ETL Básico',
      description: 'Patrón Extract, Transform, Load',
      nodeSequence: ['start', 'step', 'step', 'step', 'end'],
      frequency: 85,
      domain: 'data',
    },
    {
      id: 'pattern-2',
      name: 'Decisión Binaria',
      description: 'Flujo con decisión que diverge en dos caminos',
      nodeSequence: ['start', 'step', 'decision', 'step', 'end'],
      frequency: 75,
      domain: 'general',
    },
    {
      id: 'pattern-3',
      name: 'Procesamiento Paralelo',
      description: 'Dividir trabajo, procesar en paralelo, unir resultados',
      nodeSequence: ['start', 'split', 'step', 'step', 'join', 'step', 'end'],
      frequency: 60,
      domain: 'data',
    },
    {
      id: 'pattern-4',
      name: 'Validación en Cascada',
      description: 'Validaciones múltiples antes del final',
      nodeSequence: [
        'start',
        'step',
        'decision',
        'decision',
        'decision',
        'end',
      ],
      frequency: 55,
      domain: 'qa',
    },
  ];

  // Sugerencias predefinidas por contexto
  private contextualSuggestions = signal<Map<string, NodeSuggestion[]>>(
    new Map()
  );

  constructor(private http: HttpClient) {
    this.initializeContextualSuggestions();
  }

  /**
   * Obtener sugerencias de nodos para el siguiente paso
   */
  getNodeSuggestions(
    currentNodes: string[],
    domain: string = 'general'
  ): Observable<NodeSuggestion[]> {
    // Intentar obtener del servidor
    return this.http
      .post<NodeSuggestion[]>(`${this.apiUrl}/nodes`, {
        currentNodes,
        domain,
      })
      .pipe(
        catchError(() => {
          // Fallback a sugerencias locales
          return of(this.getLocalSuggestions(currentNodes, domain));
        })
      );
  }

  /**
   * Obtener patrones recomendados basados en historial
   */
  getRecommendedPatterns(
    domain: string = 'general'
  ): Observable<FlowPattern[]> {
    return of(
      this.commonPatterns
        .filter((p) => p.domain === domain || p.domain === 'general')
        .sort((a, b) => b.frequency - a.frequency)
        .slice(0, 3)
    );
  }

  /**
   * Evaluar calidad de un flujo completo
   */
  evaluateFlow(nodeSequence: string[]): Observable<{
    score: number;
    issues: string[];
    suggestions: string[];
  }> {
    return of(this.getLocalFlowEvaluation(nodeSequence));
  }

  /**
   * Generar nombre automático basado en contexto
   */
  generateNodeName(nodeType: string, context: string[]): Observable<string[]> {
    const suggestions: Record<string, string[]> = {
      start: [
        'Inicio del Flujo',
        'Comenzar Proceso',
        'Entrada de Datos',
        'Inicializar Flujo',
      ],
      step: [
        'Procesar Datos',
        'Validar Entrada',
        'Transformar',
        'Ejecutar Tarea',
        'Enriquecer Datos',
      ],
      decision: [
        '¿Datos válidos?',
        '¿Cumple condición?',
        'Validar Estado',
        'Evaluar Criterio',
      ],
      end: ['Finalizar', 'Completado', 'Resultado', 'Fin del Proceso'],
      join: ['Consolidar', 'Mergear Resultados', 'Unir Datos'],
      split: ['Dividir Flujo', 'Paralelizar', 'Distribuir Tarea'],
    };

    return of(suggestions[nodeType] || []);
  }

  /**
   * Detectar patrón en secuencia de nodos
   */
  detectPattern(nodeSequence: string[]): Observable<FlowPattern | null> {
    const detected = this.commonPatterns.find((p) => {
      const sequence = nodeSequence.map((id) => id.split('-')[0]); // Extraer tipo
      return JSON.stringify(p.nodeSequence) === JSON.stringify(sequence);
    });

    return of(detected || null);
  }

  /**
   * Obtener sugerencias locales (sin API)
   */
  private getLocalSuggestions(
    currentNodes: string[],
    domain: string
  ): NodeSuggestion[] {
    const suggestions: NodeSuggestion[] = [];

    // Lógica según el dominio y nodos actuales
    if (currentNodes.length === 0) {
      // Primer nodo debe ser start
      suggestions.push({
        id: 'suggest-start',
        type: 'start',
        title: 'Inicio del Flujo',
        description: 'Comienza el flujo',
        confidence: 1.0,
        reason: 'Los flujos siempre comienzan con un nodo de inicio',
        aiGenerated: true,
      });
    } else if (currentNodes[currentNodes.length - 1] === 'start') {
      // Después de start, sugerir step o decision
      suggestions.push(
        {
          id: 'suggest-step',
          type: 'step',
          title: 'Procesar Datos',
          description: 'Ejecuta una tarea o transformación',
          confidence: 0.85,
          reason: 'Los pasos son comunes después del inicio',
          aiGenerated: true,
        },
        {
          id: 'suggest-decision',
          type: 'decision',
          title: 'Validación Inicial',
          description: 'Valida las entradas',
          confidence: 0.6,
          reason: 'A menudo hay validación temprana',
          aiGenerated: true,
        }
      );
    } else if (
      currentNodes[currentNodes.length - 1] === 'step' ||
      currentNodes[currentNodes.length - 1] === 'join'
    ) {
      // Después de step o join, sugerir más steps, decision o end
      suggestions.push(
        {
          id: 'suggest-step-2',
          type: 'step',
          title: 'Siguiente Paso',
          description: 'Continúa procesando',
          confidence: 0.7,
          reason: 'Los steps pueden encadenarse',
          aiGenerated: true,
        },
        {
          id: 'suggest-decision',
          type: 'decision',
          title: 'Validar Resultado',
          description: 'Verifica el resultado del paso',
          confidence: 0.65,
          reason: 'Comúnmente se valida después de procesamiento',
          aiGenerated: true,
        },
        {
          id: 'suggest-end',
          type: 'end',
          title: 'Finalizar',
          description: 'Termina el flujo',
          confidence: 0.5,
          reason: 'El flujo puede terminar aquí',
          aiGenerated: true,
        }
      );
    } else if (currentNodes[currentNodes.length - 1] === 'decision') {
      // Después de decision, sugerir split (si hay múltiples caminos) o steps
      suggestions.push(
        {
          id: 'suggest-split',
          type: 'split',
          title: 'Divergir Caminos',
          description: 'Bifurca el flujo según la decisión',
          confidence: 0.8,
          reason: 'Las decisiones típicamente divergen',
          aiGenerated: true,
        },
        {
          id: 'suggest-step-decision',
          type: 'step',
          title: 'Camino Verdadero',
          description: 'Ejecuta si se cumple la condición',
          confidence: 0.75,
          reason: 'Uno de los caminos de la decisión',
          aiGenerated: true,
        }
      );
    }

    return suggestions.sort((a, b) => b.confidence - a.confidence);
  }

  /**
   * Evaluar un flujo localmente
   */
  private getLocalFlowEvaluation(nodeSequence: string[]): {
    score: number;
    issues: string[];
    suggestions: string[];
  } {
    let score = 100;
    const issues: string[] = [];
    const suggestions: string[] = [];

    // Validar que comience con start
    if (nodeSequence[0] !== 'start') {
      score -= 20;
      issues.push('El flujo debe comenzar con un nodo de inicio');
      suggestions.push('Agrega un nodo de inicio al principio');
    }

    // Validar que termine con end
    if (nodeSequence[nodeSequence.length - 1] !== 'end') {
      score -= 15;
      issues.push('El flujo debe terminar con un nodo de fin');
      suggestions.push('Agrega un nodo de fin al final');
    }

    // Validar longitud mínima
    if (nodeSequence.length < 3) {
      score -= 10;
      issues.push('El flujo es muy corto');
      suggestions.push('Considera agregar más pasos para lógica completa');
    }

    // Validar que hay decisiones sin split
    const decisions = nodeSequence.filter((n) => n === 'decision').length;
    const splits = nodeSequence.filter((n) => n === 'split').length;
    if (decisions > 0 && splits === 0) {
      score -= 5;
      suggestions.push('Considera usar splits para divergencias claras');
    }

    return { score: Math.max(0, score), issues, suggestions };
  }

  /**
   * Inicializar sugerencias contextuales
   */
  private initializeContextualSuggestions(): void {
    const map = new Map<string, NodeSuggestion[]>();

    // Sugerencias después de "start"
    map.set('start', [
      {
        id: 'after-start-1',
        type: 'step',
        title: 'Procesar Datos',
        confidence: 0.9,
        reason: 'Paso común después del inicio',
        aiGenerated: true,
      },
      {
        id: 'after-start-2',
        type: 'decision',
        title: 'Validar Entrada',
        confidence: 0.7,
        reason: 'Validación temprana es recomendada',
        aiGenerated: true,
      },
    ]);

    // Sugerencias después de "step"
    map.set('step', [
      {
        id: 'after-step-1',
        type: 'decision',
        title: 'Validar Resultado',
        confidence: 0.8,
        reason: 'Validar después de procesamiento',
        aiGenerated: true,
      },
      {
        id: 'after-step-2',
        type: 'step',
        title: 'Siguiente Paso',
        confidence: 0.6,
        reason: 'Los steps pueden encadenarse',
        aiGenerated: true,
      },
    ]);

    this.contextualSuggestions.set(map);
  }
}
