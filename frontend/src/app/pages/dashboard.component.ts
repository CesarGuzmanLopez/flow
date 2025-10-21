import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Flow } from '../models';
import { FlowService } from '../services/flow.service';
@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="dashboard">
      <header class="dashboard-header">
        <h1>ChemFlow Dashboard</h1>
        <button (click)="createNewFlow()">+ New Flow</button>
      </header>

      <div class="dashboard-content">
        @if (loading()) {
          <div class="loading">Loading flows...</div>
        } @else if (flows().length === 0) {
          <div class="empty-state">
            <h2>No flows yet</h2>
            <p>Create your first flow to get started</p>
            <button (click)="createNewFlow()">Create Flow</button>
          </div>
        } @else {
          <div class="flows-grid">
            @for (flow of flows(); track flow.id) {
              <div class="flow-card" (click)="openFlow(flow.id)">
                <h3>{{ flow.name }}</h3>
                <p>{{ flow.description || 'No description' }}</p>
                <div class="flow-meta">
                  <span>Version: {{ flow.current_version?.version_number || 1 }}</span>
                  <span>{{ flow.updated_at | date: 'short' }}</span>
                </div>
              </div>
            }
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
    .dashboard {
      min-height: 100vh;
      background: #f5f7fa;
    }

    .dashboard-header {
      background: white;
      padding: 1.5rem 2rem;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    h1 {
      margin: 0;
      color: #333;
    }

    button {
      padding: 0.75rem 1.5rem;
      background: #667eea;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 1rem;
    }

    button:hover {
      background: #5568d3;
    }

    .dashboard-content {
      padding: 2rem;
    }

    .loading {
      text-align: center;
      padding: 3rem;
      color: #666;
    }

    .empty-state {
      text-align: center;
      padding: 3rem;
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .empty-state h2 {
      color: #333;
      margin-bottom: 0.5rem;
    }

    .empty-state p {
      color: #666;
      margin-bottom: 1.5rem;
    }

    .flows-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 1.5rem;
    }

    .flow-card {
      background: white;
      padding: 1.5rem;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      cursor: pointer;
      transition: transform 0.2s, box-shadow 0.2s;
    }

    .flow-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    }

    .flow-card h3 {
      margin: 0 0 0.5rem 0;
      color: #333;
    }

    .flow-card p {
      color: #666;
      margin: 0 0 1rem 0;
    }

    .flow-meta {
      display: flex;
      justify-content: space-between;
      font-size: 0.875rem;
      color: #999;
    }
  `]
})
export class DashboardComponent implements OnInit {
  private readonly flowService = inject(FlowService);
  private readonly router = inject(Router);

  flows = signal<Flow[]>([]);
  loading = signal(true);

  ngOnInit(): void {
    this.loadFlows();
  }

  loadFlows(): void {
    this.loading.set(true);
    this.flowService.getFlows().subscribe({
      next: (response) => {
        this.flows.set(response.results);
        this.loading.set(false);
      },
      error: (error) => {
        console.error('Failed to load flows:', error);
        this.loading.set(false);
      }
    });
  }

  createNewFlow(): void {
    this.router.navigate(['/editor/new']);
  }

  openFlow(id: number): void {
    this.router.navigate(['/editor', id]);
  }
}
