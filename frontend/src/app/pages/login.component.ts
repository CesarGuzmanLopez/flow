import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="login-container">
      <div class="login-card">
        <h1>ChemFlow Login</h1>
        <form (ngSubmit)="onSubmit()">
          <div class="form-group">
            <label for="username">Username</label>
            <input
              type="text"
              id="username"
              [(ngModel)]="username"
              name="username"
              required
            />
          </div>
          <div class="form-group">
            <label for="password">Password</label>
            <input
              type="password"
              id="password"
              [(ngModel)]="password"
              name="password"
              required
            />
          </div>
          <div *ngIf="errorMessage()" class="error">{{ errorMessage() }}</div>
          <button type="submit" [disabled]="loading()">
            {{ loading() ? 'Loading...' : 'Login' }}
          </button>
        </form>
      </div>
    </div>
  `,
  styles: [
    `
      .login-container {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      }

      .login-card {
        background: white;
        padding: 2rem;
        border-radius: 8px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        width: 100%;
        max-width: 400px;
      }

      h1 {
        margin-bottom: 1.5rem;
        color: #333;
      }

      .form-group {
        margin-bottom: 1rem;
      }

      label {
        display: block;
        margin-bottom: 0.5rem;
        color: #555;
        font-weight: 500;
      }

      input {
        width: 100%;
        padding: 0.75rem;
        border: 1px solid #ddd;
        border-radius: 4px;
        font-size: 1rem;
      }

      input:focus {
        outline: none;
        border-color: #667eea;
      }

      button {
        width: 100%;
        padding: 0.75rem;
        background: #667eea;
        color: white;
        border: none;
        border-radius: 4px;
        font-size: 1rem;
        cursor: pointer;
        transition: background 0.3s;
      }

      button:hover:not(:disabled) {
        background: #5568d3;
      }

      button:disabled {
        background: #ccc;
        cursor: not-allowed;
      }

      .error {
        color: #e53e3e;
        margin-bottom: 1rem;
        padding: 0.5rem;
        background: #fff5f5;
        border-radius: 4px;
      }
    `,
  ],
})
export class LoginComponent {
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  username = '';
  password = '';
  loading = signal(false);
  errorMessage = signal('');

  onSubmit(): void {
    if (!this.username || !this.password) {
      this.errorMessage.set('Please enter username and password');
      return;
    }

    this.loading.set(true);
    this.errorMessage.set('');

    this.authService
      .login({ username: this.username, password: this.password })
      .subscribe({
        next: () => {
          this.router.navigate(['/dashboard']);
        },
        error: (error) => {
          this.loading.set(false);
          this.errorMessage.set(
            error.error?.detail || 'Login failed. Please try again.'
          );
        },
        complete: () => {
          this.loading.set(false);
        },
      });
  }
}
