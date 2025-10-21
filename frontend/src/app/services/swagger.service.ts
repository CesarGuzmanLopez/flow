import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_PREFIX } from '../config';

@Injectable({ providedIn: 'root' })
export class SwaggerService {
  private readonly http = inject(HttpClient);

  schema(): Observable<any> {
    return this.http.get(`${API_PREFIX}/schema/`);
  }

  // Swagger UI and Redoc are served as HTML pages; these methods return the page HTML if needed.
  swaggerUi(): Observable<string> {
    return this.http.get(`${API_PREFIX}/docs/swagger/`, {
      responseType: 'text',
    });
  }

  redoc(): Observable<string> {
    return this.http.get(`${API_PREFIX}/docs/redoc/`, { responseType: 'text' });
  }
}
