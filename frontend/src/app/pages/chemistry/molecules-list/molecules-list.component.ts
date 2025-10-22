import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Molecule } from '../../../api/model/models';
import { ChemistryAppService } from '../../../services/chemistry-app.service';
import {
  DataTableComponent,
  TableColumn,
} from '../../../shared/components/data-table/data-table.component';

/**
 * Molecules list page with search and filtering.
 */
@Component({
  selector: 'app-molecules-list',
  standalone: true,
  imports: [CommonModule, DataTableComponent],
  templateUrl: './molecules-list.component.html',
  styleUrls: ['./molecules-list.component.scss'],
})
export class MoleculesListComponent implements OnInit {
  private readonly chemService = inject(ChemistryAppService);
  private readonly router = inject(Router);

  molecules = signal<Molecule[]>([]);
  loading = signal(false);
  error = signal<string | null>(null);

  columns: TableColumn[] = [
    { key: 'id', label: 'ID', type: 'number' },
    { key: 'name', label: 'Nombre' },
    { key: 'smiles', label: 'SMILES' },
    { key: 'inchi', label: 'InChI' },
    { key: 'created_at', label: 'Creada', type: 'date' },
  ];

  ngOnInit(): void {
    this.loadMolecules();
  }

  loadMolecules(): void {
    this.loading.set(true);
    this.chemService.listMolecules().subscribe({
      next: (list) => {
        this.molecules.set(list);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err?.message || 'Error al cargar moléculas');
        this.loading.set(false);
      },
    });
  }

  onRowClick(molecule: Molecule) {
    this.router.navigate(['/chemistry/molecules', molecule.id]);
  }
}
