import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { FlowsAppService } from '../../../services/flows.service';
import { ConfirmDialogComponent } from '../../../shared/components/confirm-dialog/confirm-dialog.component';
import {
  DataTableComponent,
  TableColumn,
} from '../../../shared/components/data-table/data-table.component';
import { JsonInputComponent } from '../../../shared/components/json-input/json-input.component';
import { JsonViewerComponent } from '../../../shared/components/json-viewer/json-viewer.component';
import { ModalComponent } from '../../../shared/components/modal/modal.component';
import { PaginatorComponent } from '../../../shared/components/paginator/paginator.component';

@Component({
  selector: 'app-artifacts',
  standalone: true,
  imports: [
    CommonModule,
    DataTableComponent,
    PaginatorComponent,
    ModalComponent,
    ConfirmDialogComponent,
    JsonInputComponent,
    JsonViewerComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './artifacts.component.html',
  styleUrls: ['./artifacts.component.scss'],
})
export class ArtifactsComponent implements OnInit {
  private readonly flows = inject(FlowsAppService);

  artifacts = signal<any[]>([]);
  loading = signal(false);
  error = signal<string | null>(null);
  currentPage = signal(1);
  pageSize = signal(20);
  total = signal(0);
  searchQuery = signal('');
  selected = signal<any | null>(null);
  showCreate = signal(false);
  showEdit = signal(false);
  showDelete = signal(false);
  formData = signal<any>({});

  columns: TableColumn[] = [
    { key: 'id', label: 'ID', type: 'number' },
    { key: 'step_execution_id', label: 'Step Exec ID', type: 'number' },
    { key: 'content_hash', label: 'Hash', type: 'text' },
    { key: 'size_bytes', label: 'Tamaño (bytes)', type: 'number' },
    { key: 'created_at', label: 'Creado', type: 'date' },
  ];

  ngOnInit(): void {
    this.loadArtifacts();
  }

  loadArtifacts(): void {
    this.loading.set(true);
    const offset = (this.currentPage() - 1) * this.pageSize();
    this.flows.getArtifacts({ limit: this.pageSize(), offset }).subscribe({
      next: (list: any) => {
        this.artifacts.set(list || []);
        this.total.set(list.length);
        this.loading.set(false);
      },
      error: (err: any) => {
        this.error.set(err?.message || 'Error cargando artifacts');
        this.loading.set(false);
      },
    });
  }

  download(artifactId: number): void {
    this.flows.downloadArtifact(artifactId).subscribe({
      next: (blob: Blob) => {
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `artifact-${artifactId}`;
        a.click();
        URL.revokeObjectURL(a.href);
      },
      error: (err: any) => this.error.set('Error descargando artifact'),
    });
  }

  onRowClick(row: any): void {
    this.selected.set(row);
  }

  onPageChange(page: number): void {
    this.currentPage.set(page);
    this.loadArtifacts();
  }

  onPageSizeChange(size: number): void {
    this.pageSize.set(size);
    this.currentPage.set(1);
    this.loadArtifacts();
  }

  // CRUD helpers
  openCreate(): void {
    this.formData.set({});
    this.showCreate.set(true);
  }

  openEdit(): void {
    if (!this.selected()) return;
    this.formData.set(this.selected());
    this.showEdit.set(true);
  }

  openDelete(): void {
    if (!this.selected()) return;
    this.showDelete.set(true);
  }

  closeModals(): void {
    this.showCreate.set(false);
    this.showEdit.set(false);
    this.showDelete.set(false);
  }

  create(): void {
    this.loading.set(true);
    this.flows.createArtifact(this.formData()).subscribe({
      next: () => {
        this.loading.set(false);
        this.showCreate.set(false);
        this.loadArtifacts();
      },
      error: (err: any) => {
        this.loading.set(false);
        this.error.set(err?.message || 'Error creando artifact');
      },
    });
  }

  update(): void {
    const sel = this.selected();
    if (!sel?.id) return;
    this.loading.set(true);
    this.flows.updateArtifact(sel.id, this.formData()).subscribe({
      next: () => {
        this.loading.set(false);
        this.showEdit.set(false);
        this.loadArtifacts();
      },
      error: (err: any) => {
        this.loading.set(false);
        this.error.set(err?.message || 'Error actualizando artifact');
      },
    });
  }

  remove(): void {
    const sel = this.selected();
    if (!sel?.id) return;
    this.loading.set(true);
    this.flows.deleteArtifact(sel.id).subscribe({
      next: () => {
        this.loading.set(false);
        this.showDelete.set(false);
        this.selected.set(null);
        this.loadArtifacts();
      },
      error: (err: any) => {
        this.loading.set(false);
        this.error.set(err?.message || 'Error eliminando artifact');
      },
    });
  }
}
