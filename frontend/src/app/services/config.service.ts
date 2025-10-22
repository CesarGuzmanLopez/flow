import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

/**
 * Config service for loading runtime API base from assets/backend.json
 * Falls back to hardcoded config.ts value if file not found or empty.
 */
@Injectable({ providedIn: 'root' })
export class ConfigService {
  private readonly http = inject(HttpClient);

  private cachedApiBase: string | null = null;

  async loadApiBase(): Promise<string> {
    if (this.cachedApiBase) {
      return this.cachedApiBase;
    }

    try {
      const config = await firstValueFrom(
        this.http.get<{ apiBase?: string }>('/assets/backend.json')
      );
      if (config?.apiBase) {
        this.cachedApiBase = config.apiBase;
        return config.apiBase;
      }
    } catch (err) {
      console.warn(
        'Could not load assets/backend.json, falling back to default'
      );
    }

    // Fallback to default from config.ts
    return 'http://127.0.0.1:8000';
  }
}
