import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss'],
})
export class LoginComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  username = signal('');
  password = signal('');
  loading = signal(false);
  error = signal<string | null>(null);

  submit(): void {
    this.error.set(null);
    this.loading.set(true);
    this.auth
      .login({ username: this.username(), password: this.password() })
      .subscribe({
        next: () => {
          this.loading.set(false);
          const returnUrl = new URLSearchParams(window.location.search).get(
            'returnUrl'
          );
          this.router.navigate([returnUrl || '/dashboard']);
        },
        error: (err) => {
          this.loading.set(false);
          this.error.set(
            err?.error?.detail || err?.message || 'Credenciales inválidas'
          );
        },
      });
  }
}
