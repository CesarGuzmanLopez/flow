import { CommonModule, NgForOf, NgIf } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { FlowsAppService } from '../../../services/flows.service';
import { ConfirmDialogComponent } from '../../../shared/components/confirm-dialog/confirm-dialog.component';
import { ModalComponent } from '../../../shared/components/modal/modal.component';

@Component({
  selector: 'app-branch-management',
  standalone: true,
  imports: [
    CommonModule,
    NgIf,
    NgForOf,
    FormsModule,
    ReactiveFormsModule,
    RouterModule,
    ModalComponent,
    ConfirmDialogComponent,
  ],
  templateUrl: './branch-management.component.html',
  styleUrls: ['./branch-management.component.scss'],
})
export class BranchManagementComponent implements OnInit {
  private flows = inject(FlowsAppService);
  private route = inject(ActivatedRoute);

  // State
  branches = signal<any[]>([]);
  loading = signal(false);
  error = signal<string | null>(null);
  flowId = signal<number | null>(null);

  // Modal state for create
  showCreateModal = signal(false);
  branchName = signal('');
  selectedParentBranch = signal<number | null>(null);

  // Confirm dialog
  showConfirmDelete = signal(false);
  branchToDelete = signal<any | null>(null);

  // Columns for table
  columns = [
    { key: 'id', label: 'ID' },
    { key: 'name', label: 'Nombre' },
    { key: 'parent_id', label: 'Rama Padre' },
    { key: 'created_at', label: 'Creada' },
    { key: 'updated_at', label: 'Actualizada' },
  ];

  // Computed
  otherBranches = computed(() =>
    this.branches().filter((b) => b.id !== this.branchToDelete()?.id)
  );

  ngOnInit(): void {
    this.route.queryParams.subscribe((params) => {
      if (params['flowId']) {
        this.flowId.set(parseInt(params['flowId'], 10));
        this.loadBranches();
      }
    });
  }

  // Exposed for template retry
  loadBranches(): void {
    this.loading.set(true);
    this.error.set(null);

    this.flows.listBranches().subscribe({
      next: (branches: any) => {
        this.branches.set(branches);
        this.loading.set(false);
      },
      error: (err: any) => {
        this.error.set('Error cargando ramas');
        this.loading.set(false);
        console.error(err);
      },
    });
  }

  onCreateClick(): void {
    this.branchName.set('');
    this.selectedParentBranch.set(null);
    this.showCreateModal.set(true);
  }

  onCreateBranch(): void {
    if (!this.branchName() || !this.flowId()) {
      this.error.set('Nombre de rama es requerido');
      return;
    }

    this.loading.set(true);

    const data = {
      name: this.branchName(),
      parent_id: this.selectedParentBranch(),
    };

    this.flows.createBranch(this.flowId()!, data).subscribe({
      next: () => {
        this.showCreateModal.set(false);
        this.loadBranches();
      },
      error: (err: any) => {
        this.error.set('Error creando rama');
        this.loading.set(false);
        console.error(err);
      },
    });
  }

  onDeleteClick(branch: any): void {
    this.branchToDelete.set(branch);
    this.showConfirmDelete.set(true);
  }

  onConfirmDelete(): void {
    if (!this.branchToDelete()) return;

    this.loading.set(true);
    const branchId = this.branchToDelete()!.id;

    this.flows.deleteBranch(branchId).subscribe({
      next: () => {
        this.showConfirmDelete.set(false);
        this.branchToDelete.set(null);
        this.loadBranches();
      },
      error: (err: any) => {
        this.error.set('Error eliminando rama');
        this.loading.set(false);
        console.error(err);
      },
    });
  }

  onCancelCreate(): void {
    this.showCreateModal.set(false);
    this.branchName.set('');
    this.selectedParentBranch.set(null);
  }

  onSelectParent(value: string | number | null): void {
    const id = value === null || value === 'null' ? null : Number(value);
    this.selectedParentBranch.set(id);
  }
}
