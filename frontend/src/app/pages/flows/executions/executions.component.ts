import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { FlowsAppService } from '../../../services/flows.service';
import {
  DataTableComponent,
  TableColumn,
} from '../../../shared/components/data-table/data-table.component';
import { PaginatorComponent } from '../../../shared/components/paginator/paginator.component';
import { SseLogViewerComponent } from '../../../shared/components/sse-log-viewer/sse-log-viewer.component';

@Component({
  selector: 'app-executions',
  standalone: true,
  imports: [
    CommonModule,
    DataTableComponent,
    SseLogViewerComponent,
    PaginatorComponent,
  ],
  templateUrl: './executions.component.html',
  styleUrls: ['./executions.component.scss'],
})
export class ExecutionsComponent implements OnInit {
  private readonly flows = inject(FlowsAppService);
  private readonly route = inject(ActivatedRoute);

  executions = signal<any[]>([]);
  selectedExecution = signal<any | null>(null);
  stepExecutions = signal<any[]>([]);
  loading = signal(false);
  error = signal<string | null>(null);
  currentPage = signal(1);
  pageSize = signal(20);
  total = signal(0);

  columns: TableColumn[] = [
    { key: 'id', label: 'ID', type: 'number' },
    { key: 'flow_id', label: 'Flow ID', type: 'number' },
    {
      key: 'status',
      label: 'Estado',
      type: 'badge',
      badgeClass: (v: any) => `badge ${v}`,
    },
    { key: 'created_at', label: 'Creada', type: 'date' },
    { key: 'completed_at', label: 'Completada', type: 'date' },
  ];

  stepColumns: TableColumn[] = [
    { key: 'id', label: 'ID', type: 'number' },
    { key: 'step_type', label: 'Tipo', type: 'text' },
    { key: 'status', label: 'Estado', type: 'badge' },
    { key: 'started_at', label: 'Inicio', type: 'date' },
    { key: 'completed_at', label: 'Fin', type: 'date' },
  ];

  ngOnInit(): void {
    this.loadExecutions();
  }

  loadExecutions(): void {
    this.loading.set(true);
    const offset = (this.currentPage() - 1) * this.pageSize();
    this.flows.listExecutions({ limit: this.pageSize(), offset }).subscribe({
      next: (data) => {
        const list = Array.isArray(data) ? data : data?.results ?? [];
        const count = (data as any)?.count ?? list.length;
        this.executions.set(list);
        this.total.set(count);
        this.loading.set(false);
      },
      error: (err: any) => {
        this.error.set(err?.message || 'Error cargando ejecuciones');
        this.loading.set(false);
      },
    });
  }

  onSelectExecution(exec: any): void {
    this.selectedExecution.set(exec);
    if (exec?.id) {
      this.flows.getExecutionSteps(exec.id).subscribe({
        next: (data) => {
          this.stepExecutions.set((data as any)?.steps ?? []);
        },
      });
    }
  }

  downloadArtifact(artifactId: number): void {
    this.flows.getArtifactDownloadUrl(artifactId).subscribe({
      next: (blob: any) => {
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `artifact-${artifactId}`;
        a.click();
      },
      error: (err: any) => this.error.set('Error descargando artifact'),
    });
  }

  onPageChange(page: number): void {
    this.currentPage.set(page);
    this.loadExecutions();
  }

  onPageSizeChange(size: number): void {
    this.pageSize.set(size);
    this.currentPage.set(1);
    this.loadExecutions();
  }
}
