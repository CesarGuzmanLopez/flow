import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_PREFIX } from '../config';
import { Permission, Role, User } from '../models';

@Injectable({ providedIn: 'root' })
export class UsersService {
  private readonly http = inject(HttpClient);
  private readonly base = `${API_PREFIX}/users`;

  getUsers(params?: any): Observable<{ results: User[]; count: number }> {
    return this.http.get<{ results: User[]; count: number }>(
      `${this.base}/users/`,
      { params }
    );
  }

  getUser(id: number): Observable<User> {
    return this.http.get<User>(`${this.base}/users/${id}/`);
  }

  getRoles(): Observable<Role[]> {
    return this.http.get<Role[]>(`${this.base}/roles/`);
  }

  getPermissions(): Observable<Permission[]> {
    return this.http.get<Permission[]>(`${this.base}/permissions/`);
  }
}
