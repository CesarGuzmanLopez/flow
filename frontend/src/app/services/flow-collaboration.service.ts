import { Injectable, signal } from '@angular/core';
import { Subject } from 'rxjs';

/**
 * Interfaz para la presencia de un usuario en el flujo
 */
export interface UserPresence {
  user_id: number;
  username: string;
  flow_id: number;
  cursor_position: { x: number; y: number };
  selected_node_id: string | null;
  locked_elements: string[];
}

/**
 * Interfaz para mensajes de cambio en nodos
 */
export interface NodeChangeMessage {
  user_id: number;
  username: string;
  node_id: string;
  node_data: any;
  operation: 'create' | 'update' | 'delete';
}

/**
 * Interfaz para mensajes de cursor compartido
 */
export interface CursorMessage {
  user_id: number;
  username: string;
  position: { x: number; y: number };
}

/**
 * Interfaz para mensajes de lock de elemento
 */
export interface LockMessage {
  user_id: number;
  username: string;
  element_id: string;
}

/**
 * Servicio para colaboración en tiempo real en flujos
 *
 * Gestiona:
 * - Conexión WebSocket al servidor
 * - Sincronización de cambios
 * - Presencia de usuarios
 * - Locks de elementos
 * - Cursores compartidos
 */
@Injectable({
  providedIn: 'root',
})
export class FlowCollaborationService {
  private websocket: WebSocket | null = null;
  private flowId: number | null = null;
  private userId: number | null = null;
  private username: string = 'anonymous';

  // Señales para estado reactivo
  isConnected = signal<boolean>(false);
  remoteUsers = signal<UserPresence[]>([]);
  lockedElements = signal<Map<string, number>>(new Map());

  // Observables para eventos
  private nodeChangedSubject = new Subject<NodeChangeMessage>();
  public nodeChanged$ = this.nodeChangedSubject.asObservable();

  private cursorMovedSubject = new Subject<CursorMessage>();
  public cursorMoved$ = this.cursorMovedSubject.asObservable();

  private elementLockedSubject = new Subject<LockMessage>();
  public elementLocked$ = this.elementLockedSubject.asObservable();

  private elementUnlockedSubject = new Subject<LockMessage>();
  public elementUnlocked$ = this.elementUnlockedSubject.asObservable();

  private nodeSelectedSubject = new Subject<any>();
  public nodeSelected$ = this.nodeSelectedSubject.asObservable();

  private errorSubject = new Subject<string>();
  public error$ = this.errorSubject.asObservable();

  constructor() {}

  /**
   * Conectar al servidor WebSocket para un flujo específico
   */
  connect(flowId: number, userId?: number, username?: string): void {
    if (this.websocket) {
      console.warn('Ya conectado a WebSocket');
      return;
    }

    this.flowId = flowId;
    this.userId = userId || 0;
    this.username = username || 'anonymous';

    // Determinar protocolo (ws o wss)
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/flows/${flowId}/`;

    try {
      this.websocket = new WebSocket(wsUrl);

      this.websocket.onopen = () => {
        console.log(`Conectado al flujo ${flowId}`);
        this.isConnected.set(true);
      };

      this.websocket.onmessage = (event) => {
        this.handleMessage(JSON.parse(event.data));
      };

      this.websocket.onerror = (error) => {
        console.error('Error en WebSocket:', error);
        this.errorSubject.next('Error en conexión WebSocket');
      };

      this.websocket.onclose = () => {
        console.log('Desconectado de WebSocket');
        this.isConnected.set(false);
        this.websocket = null;
      };
    } catch (error) {
      console.error('No se pudo conectar a WebSocket:', error);
      this.errorSubject.next('No se pudo conectar al servidor');
    }
  }

  /**
   * Desconectar del servidor WebSocket
   */
  disconnect(): void {
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
      this.isConnected.set(false);
    }
  }

  /**
   * Enviar cambio de nodo
   */
  broadcastNodeChange(
    nodeId: string,
    nodeData: any,
    operation: 'create' | 'update' | 'delete'
  ): void {
    this.sendMessage({
      type: 'node_changed',
      node_id: nodeId,
      node_data: nodeData,
      operation: operation,
    });
  }

  /**
   * Enviar posición del cursor
   */
  broadcastCursorPosition(x: number, y: number): void {
    this.sendMessage({
      type: 'cursor_moved',
      position: { x, y },
    });
  }

  /**
   * Solicitar lock de elemento
   */
  lockElement(elementId: string): void {
    this.sendMessage({
      type: 'lock_element',
      element_id: elementId,
    });
  }

  /**
   * Liberar lock de elemento
   */
  unlockElement(elementId: string): void {
    this.sendMessage({
      type: 'unlock_element',
      element_id: elementId,
    });
  }

  /**
   * Notificar selección de nodo
   */
  broadcastNodeSelection(nodeId: string | null): void {
    this.sendMessage({
      type: 'select_node',
      node_id: nodeId,
    });
  }

  /**
   * Enviar mensaje por WebSocket
   */
  private sendMessage(data: any): void {
    if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket no conectado');
      return;
    }

    try {
      this.websocket.send(JSON.stringify(data));
    } catch (error) {
      console.error('Error al enviar mensaje:', error);
    }
  }

  /**
   * Procesar mensajes recibidos del servidor
   */
  private handleMessage(message: any): void {
    const { type, data } = message;

    switch (type) {
      case 'user_joined':
        this.handleUserJoined(data);
        break;

      case 'user_left':
        this.handleUserLeft(data);
        break;

      case 'node_changed':
        this.nodeChangedSubject.next(data);
        break;

      case 'cursor_moved':
        this.cursorMovedSubject.next(data);
        break;

      case 'element_locked':
        this.elementLockedSubject.next(data);
        this.updateLockedElements();
        break;

      case 'element_unlocked':
        this.elementUnlockedSubject.next(data);
        this.updateLockedElements();
        break;

      case 'node_selected':
        this.nodeSelectedSubject.next(data);
        break;

      case 'current_presences':
        this.remoteUsers.set(data.presences || []);
        break;

      case 'error':
        this.errorSubject.next(data.message);
        break;

      default:
        console.warn('Tipo de mensaje desconocido:', type);
    }
  }

  /**
   * Procesar usuario conectado
   */
  private handleUserJoined(data: UserPresence): void {
    const currentUsers = this.remoteUsers();
    // Evitar duplicados
    const filtered = currentUsers.filter((u) => u.user_id !== data.user_id);
    this.remoteUsers.set([...filtered, data]);
  }

  /**
   * Procesar usuario desconectado
   */
  private handleUserLeft(data: { user_id: number; username: string }): void {
    const currentUsers = this.remoteUsers();
    this.remoteUsers.set(
      currentUsers.filter((u) => u.user_id !== data.user_id)
    );
  }

  /**
   * Actualizar mapa de elementos lockeados
   */
  private updateLockedElements(): void {
    // Este método se puede extender para actualizar la señal
    // según los eventos recibidos
  }

  /**
   * Obtener si un elemento está lockeado por otro usuario
   */
  isLockedByOther(elementId: string, currentUserId?: number): boolean {
    const locks = this.lockedElements();
    const lockOwner = locks.get(elementId);
    return lockOwner != null && lockOwner !== currentUserId;
  }

  /**
   * Obtener usuario remoto por ID
   */
  getRemoteUser(userId: number): UserPresence | undefined {
    return this.remoteUsers().find((u) => u.user_id === userId);
  }

  /**
   * Obtener usuarios remotos activos
   */
  getRemoteUsers(): UserPresence[] {
    return this.remoteUsers();
  }

  /**
   * Obtener información de conexión
   */
  getConnectionInfo(): {
    isConnected: boolean;
    flowId: number | null;
    userId: number | null;
    username: string;
  } {
    return {
      isConnected: this.isConnected(),
      flowId: this.flowId,
      userId: this.userId,
      username: this.username,
    };
  }
}
