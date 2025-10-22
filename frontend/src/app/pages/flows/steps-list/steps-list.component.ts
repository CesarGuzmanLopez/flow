import { CommonModule, NgIf } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { FlowsAppService } from '../../../services/flows.service';
import {
  DataTableComponent,
  TableColumn,
} from '../../../shared/components/data-table/data-table.component';
import { JsonViewerComponent } from '../../../shared/components/json-viewer/json-viewer.component';
import { PaginatorComponent } from '../../../shared/components/paginator/paginator.component';

@Component({
  selector: 'app-steps-list',
  standalone: true,
  imports: [
    CommonModule,
    NgIf,
    FormsModule,
    DataTableComponent,
    PaginatorComponent,
    JsonViewerComponent,
  ],
  templateUrl: './steps-list.component.html',
  styleUrls: ['./steps-list.component.scss'],
})
export class StepsListComponent implements OnInit {
  private flows = inject(FlowsAppService);

  steps = signal<any[]>([]);
  loading = signal(false);
  error = signal<string | null>(null);
  currentPage = signal(1);
  pageSize = signal(20);
  total = signal(0);
  selected = signal<any | null>(null);

  columns: TableColumn[] = [
    { key: 'id', label: 'ID', type: 'number' },
    { key: 'name', label: 'Nombre', type: 'text' },
    { key: 'provider', label: 'Proveedor', type: 'text' },
    { key: 'status', label: 'Estado', type: 'badge' },
  ];

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    const offset = (this.currentPage() - 1) * this.pageSize();
    this.flows.listSteps({ limit: this.pageSize(), offset }).subscribe({
      next: (list: any[]) => {
        this.steps.set(list);
        this.total.set(((list as any).count as number) || list.length);
        this.loading.set(false);
      },
      error: (err: any) => {
        this.error.set(err?.message || 'Error cargando pasos');
        this.loading.set(false);
      },
    });
  }

  onRowClick(row: any): void {
    this.selected.set(row);
    // Optionally fetch full step
    if (row?.id) {
      this.flows.getStep(row.id).subscribe({
        next: (full) => this.selected.set(full),
      });
    }
  }

  onPageChange(p: number): void {
    this.currentPage.set(p);
    this.load();
  }

  onPageSizeChange(size: number): void {
    this.pageSize.set(size);
    this.currentPage.set(1);
    this.load();
  }
}
