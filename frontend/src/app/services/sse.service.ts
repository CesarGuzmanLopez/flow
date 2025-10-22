import { Injectable } from '@angular/core';
import { API_PREFIX } from '../config';

export type SseMessage = { event: string; data: any };

@Injectable({ providedIn: 'root' })
export class SseService {
  private sources: Map<string | number, EventSource> = new Map();

  openStepExecutionLogs(
    stepExecutionId: string | number,
    onMessage: (msg: SseMessage) => void,
    onError?: (err: any) => void
  ): EventSource {
    const url = `${API_PREFIX}/api/flows/step-executions/${stepExecutionId}/logs/stream/`;
    const src = new EventSource(url, { withCredentials: false });

    src.onmessage = (ev: MessageEvent) => {
      try {
        const msg = JSON.parse(ev.data);
        onMessage(msg);
      } catch {
        // Heartbeats or comments
      }
    };

    src.onerror = (err) => {
      if (onError) onError(err);
    };

    this.sources.set(stepExecutionId, src);
    return src;
  }

  close(stepExecutionId: string | number): void {
    const src = this.sources.get(stepExecutionId);
    if (src) {
      src.close();
      this.sources.delete(stepExecutionId);
    }
  }
}
