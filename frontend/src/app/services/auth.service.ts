import { Injectable, inject } from '@angular/core';
import { BehaviorSubject, Observable, map, tap } from 'rxjs';
import { AutenticacinService } from '../api/api/autenticacin.service';
import { TokenService } from '../api/api/token.service';
import { TokenObtainPair } from '../api/model/tokenObtainPair';
import { TokenRefresh } from '../api/model/tokenRefresh';
import {
  LoginRequest,
  LoginResponse,
  TokenRefreshResponse,
  User,
} from '../models';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private readonly authApi = inject(AutenticacinService);
  private readonly tokenApi = inject(TokenService);

  private currentUserSubject = new BehaviorSubject<User | null>(null);
  public currentUser$ = this.currentUserSubject.asObservable();

  private tokenSubject = new BehaviorSubject<string | null>(
    this.getStoredToken()
  );
  public token$ = this.tokenSubject.asObservable();

  constructor() {
    this.loadUserFromStorage();
  }

  login(credentials: LoginRequest): Observable<LoginResponse> {
    const payload: TokenObtainPair = {
      username: credentials.username,
      password: credentials.password,
    } as TokenObtainPair;

    return this.authApi.tokenCreate(payload).pipe(
      map((resp: any) => resp as LoginResponse),
      tap((response) => {
        this.storeTokens(response.access, response.refresh);
        this.currentUserSubject.next(response.user);
        localStorage.setItem('currentUser', JSON.stringify(response.user));
      })
    );
  }

  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('currentUser');
    this.tokenSubject.next(null);
    this.currentUserSubject.next(null);
  }

  refreshToken(): Observable<TokenRefreshResponse> {
    const refresh = localStorage.getItem('refresh_token');
    const payload: TokenRefresh = { refresh } as TokenRefresh;
    return this.tokenApi.tokenRefreshCreate(payload).pipe(
      map((resp: any) => resp as TokenRefreshResponse),
      tap((response) => {
        localStorage.setItem('access_token', response.access);
        this.tokenSubject.next(response.access);
      })
    );
  }

  isAuthenticated(): boolean {
    return !!this.getStoredToken();
  }

  getToken(): string | null {
    return this.getStoredToken();
  }

  private storeTokens(access: string, refresh: string): void {
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
    this.tokenSubject.next(access);
  }

  private getStoredToken(): string | null {
    return localStorage.getItem('access_token');
  }

  private loadUserFromStorage(): void {
    const userStr = localStorage.getItem('currentUser');
    if (userStr) {
      try {
        const user = JSON.parse(userStr);
        this.currentUserSubject.next(user);
      } catch (e) {
        console.error('Failed to parse stored user', e);
      }
    }
  }
}
