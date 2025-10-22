import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { Router, RouterOutlet } from '@angular/router';
import { NavComponent } from './shared/components/nav/nav.component';

@Component({
  selector: 'app-root',
  imports: [CommonModule, RouterOutlet, NavComponent],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  private readonly router = inject(Router);
  protected title = 'frontend';

  isLoginPage(): boolean {
    return this.router.url === '/login';
  }
}
