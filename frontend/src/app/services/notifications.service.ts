import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_PREFIX } from '../config';

@Injectable({ providedIn: 'root' })
export class NotificationsService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = `${API_PREFIX}/api/notifications`;

  listNotifications(params?: any): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/`, { params });
  }

  getNotification(id: number): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/${id}/`);
  }

  markAsRead(id: number): Observable<any> {
    // Align with backend/OpenAPI path: uses underscores, not hyphens
    return this.http.post(`${this.apiUrl}/${id}/mark_as_read/`, {});
  }

  markAllAsRead(): Observable<any> {
    // Align with backend/OpenAPI path: uses underscores, not hyphens
    return this.http.post(`${this.apiUrl}/mark_all_as_read/`, {});
  }

  deleteNotification(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${id}/`);
  }
}
