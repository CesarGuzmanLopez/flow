import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Family } from '../../../api/model/models';
import { ChemistryAppService } from '../../../services/chemistry-app.service';
import {
  DataTableComponent,
  TableColumn,
} from '../../../shared/components/data-table/data-table.component';

/**
 * Families list page with search and filtering.
 */
@Component({
  selector: 'app-families-list',
  standalone: true,
  imports: [CommonModule, DataTableComponent],
  templateUrl: './families-list.component.html',
  styleUrls: ['./families-list.component.scss'],
})
export class FamiliesListComponent implements OnInit {
  private readonly chemService = inject(ChemistryAppService);
  private readonly router = inject(Router);

  families = signal<Family[]>([]);
  loading = signal(false);
  error = signal<string | null>(null);

  columns: TableColumn[] = [
    { key: 'id', label: 'ID', type: 'number' },
    { key: 'name', label: 'Nombre' },
    { key: 'provenance', label: 'Origen' },
    { key: 'created_at', label: 'Creada', type: 'date' },
  ];

  ngOnInit(): void {
    this.loadFamilies();
  }

  loadFamilies(): void {
    this.loading.set(true);
    this.chemService.listFamilies().subscribe({
      next: (list) => {
        this.families.set(list);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err?.message || 'Error al cargar familias');
        this.loading.set(false);
      },
    });
  }

  onRowClick(family: Family) {
    this.router.navigate(['/chemistry/families', family.id]);
  }
}
