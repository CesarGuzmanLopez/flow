import { CommonModule, NgForOf, NgIf } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { Step } from '../../../api/model/models';
import { FlowsAppService } from '../../../services/flows.service';
import { PaginatorComponent } from '../../../shared/components/paginator/paginator.component';

@Component({
  selector: 'app-step-catalog',
  standalone: true,
  imports: [
    CommonModule,
    NgIf,
    NgForOf,
    FormsModule,
    ReactiveFormsModule,
    RouterModule,
    PaginatorComponent,
  ],
  templateUrl: './step-catalog.component.html',
  styleUrls: ['./step-catalog.component.scss'],
})
export class StepCatalogComponent implements OnInit {
  private flows = inject(FlowsAppService);
  private router = inject(Router);

  // State
  // Use any for catalog entries because generated Step model may not include provider/inputs/outputs
  steps = signal<any[]>([]);
  loading = signal(false);
  error = signal<string | null>(null);
  searchText = signal('');
  currentPage = signal(1);
  pageSize = signal(10);
  selectedStep = signal<any | null>(null);

  // Computed
  filteredSteps = computed(() => {
    const text = this.searchText().toLowerCase();
    return this.steps().filter(
      (step) =>
        (step.name?.toLowerCase().includes(text) ?? false) ||
        (step.description?.toLowerCase().includes(text) ?? false) ||
        (step.provider?.toLowerCase().includes(text) ?? false)
    );
  });

  totalPages = computed(() =>
    Math.ceil(this.filteredSteps().length / this.pageSize())
  );

  paginatedSteps = computed(() => {
    const offset = (this.currentPage() - 1) * this.pageSize();
    return this.filteredSteps().slice(offset, offset + this.pageSize());
  });

  // Columns for table
  columns = [
    { key: 'name', label: 'Nombre' },
    { key: 'provider', label: 'Proveedor' },
    { key: 'description', label: 'Descripción' },
    { key: 'status', label: 'Estado' },
  ];

  ngOnInit(): void {
    this.loadCatalog();
  }

  // Exposed for template retry
  loadCatalog(): void {
    this.loading.set(true);
    this.error.set(null);

    this.flows.getStepCatalog().subscribe({
      next: (catalog: any) => {
        const stepsList = Array.isArray(catalog)
          ? catalog
          : catalog?.steps ?? [];
        this.steps.set(stepsList);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set('Error cargando catálogo de pasos');
        this.loading.set(false);
        console.error(err);
      },
    });
  }

  onSearch(text: string): void {
    this.searchText.set(text);
    this.currentPage.set(1);
  }

  onPageChange(page: number): void {
    this.currentPage.set(page);
  }

  onPageSizeChange(size: number): void {
    this.pageSize.set(size);
    this.currentPage.set(1);
  }

  onSelectStep(step: Step): void {
    this.selectedStep.set(step);
  }

  onExecuteStep(): void {
    if (!this.selectedStep()) return;

    const step = this.selectedStep();
    this.loading.set(true);

    this.flows.executeStep(step).subscribe({
      next: (result: any) => {
        this.loading.set(false);
        // Redirect to execution detail or show result
        console.log('Step executed:', result);
        alert(`Paso ejecutado exitosamente: ${result?.id}`);
      },
      error: (err) => {
        this.loading.set(false);
        this.error.set('Error ejecutando paso');
        console.error(err);
      },
    });
  }

  onAppendStep(): void {
    if (!this.selectedStep()) return;
    // For now, navigate to flow editor with step info
    // This would be integrated with branch management
    alert('Característica de agregar a rama en desarrollo');
  }
}
