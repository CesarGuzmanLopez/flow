import { CommonModule } from '@angular/common';
import { Component, OnInit, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ChemistryAppService } from '../../../services/chemistry-app.service';
import { ConfirmDialogComponent } from '../../../shared/components/confirm-dialog/confirm-dialog.component';
import {
  DataTableComponent,
  TableColumn,
} from '../../../shared/components/data-table/data-table.component';
import { ModalComponent } from '../../../shared/components/modal/modal.component';

@Component({
  selector: 'app-molecule-detail',
  standalone: true,
  imports: [
    CommonModule,
    DataTableComponent,
    ModalComponent,
    ConfirmDialogComponent,
  ],
  templateUrl: './molecule-detail.component.html',
  styleUrls: ['./molecule-detail.component.scss'],
})
export class MoleculeDetailComponent implements OnInit {
  molecule = signal<any>(null);
  properties = signal<any[]>([]);
  loading = signal(true);
  error = signal<string | null>(null);
  showDeleteModal = signal(false);
  showCreateProperty = signal(false);
  showEditProperty = signal(false);
  showDeleteProperty = signal(false);
  selectedProperty = signal<any | null>(null);
  propertyForm = signal<{
    property_type: string;
    value: string;
    units: string;
    method: string;
  }>({
    property_type: '',
    value: '',
    units: '',
    method: '',
  });

  propertiesColumns: TableColumn[] = [
    { key: 'property_type', label: 'Property', type: 'text' },
    { key: 'value', label: 'Value', type: 'text' },
    { key: 'units', label: 'Unit', type: 'text' },
    { key: 'method', label: 'Method', type: 'text' },
    { key: 'created_at', label: 'Calculated', type: 'date' },
    {
      key: 'actions',
      label: 'Actions',
      type: 'actions',
      actions: [
        { label: 'Edit', action: 'edit' },
        { label: 'Delete', action: 'delete' },
      ],
    },
  ];

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private chemistryService: ChemistryAppService
  ) {}

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.loadMolecule(+id);
      this.loadProperties(+id);
    }
  }

  loadMolecule(id: number): void {
    this.loading.set(true);
    this.error.set(null);

    this.chemistryService.getMolecule(id).subscribe({
      next: (data) => {
        this.molecule.set(data);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err.message || 'Failed to load molecule');
        this.loading.set(false);
      },
    });
  }

  loadProperties(moleculeId: number): void {
    // Fetch all and filter client-side until API provides filtering
    this.chemistryService.listMolecularProperties({ limit: 1000 }).subscribe({
      next: (data) => {
        const list = (data || []).filter(
          (p: any) => p.molecule_id === moleculeId
        );
        this.properties.set(list);
      },
      error: (err) => {
        console.error('Failed to load properties:', err);
      },
    });
  }

  openDeleteModal(): void {
    this.showDeleteModal.set(true);
  }

  closeDeleteModal(): void {
    this.showDeleteModal.set(false);
  }

  confirmDelete(): void {
    const mol = this.molecule();
    if (mol?.id) {
      this.chemistryService.deleteMolecule(mol.id).subscribe({
        next: () => {
          this.router.navigate(['/chemistry/molecules']);
        },
        error: (err) => {
          this.error.set(err.message || 'Failed to delete molecule');
          this.showDeleteModal.set(false);
        },
      });
    }
  }

  goBack(): void {
    this.router.navigate(['/chemistry/molecules']);
  }

  // Property CRUD
  openCreateProperty(): void {
    this.propertyForm.set({
      property_type: '',
      value: '',
      units: '',
      method: '',
    });
    this.showCreateProperty.set(true);
  }

  createProperty(): void {
    const mol = this.molecule();
    const form = this.propertyForm();
    if (!mol?.id || !form.property_type.trim()) return;
    const data: any = {
      molecule: mol.id,
      property_type: form.property_type,
      value: form.value,
      units: form.units,
      method: form.method,
    };
    this.chemistryService.createMolecularProperty(data).subscribe({
      next: () => {
        this.showCreateProperty.set(false);
        this.loadProperties(mol.id);
      },
      error: (err) =>
        this.error.set(err?.message || 'Failed to create property'),
    });
  }

  openEditProperty(prop: any): void {
    this.selectedProperty.set(prop);
    this.propertyForm.set({
      property_type: prop.property_type,
      value: prop.value,
      units: prop.units || '',
      method: prop.method || '',
    });
    this.showEditProperty.set(true);
  }

  editProperty(): void {
    const prop = this.selectedProperty();
    const form = this.propertyForm();
    if (!prop?.id || !form.property_type.trim()) return;
    const data: any = {
      property_type: form.property_type,
      value: form.value,
      units: form.units,
      method: form.method,
    };
    this.chemistryService.updateMolecularProperty(prop.id, data).subscribe({
      next: () => {
        this.showEditProperty.set(false);
        this.selectedProperty.set(null);
        const mol = this.molecule();
        if (mol?.id) this.loadProperties(mol.id);
      },
      error: (err) =>
        this.error.set(err?.message || 'Failed to update property'),
    });
  }

  openDeleteProperty(prop: any): void {
    this.selectedProperty.set(prop);
    this.showDeleteProperty.set(true);
  }

  deleteProperty(): void {
    const prop = this.selectedProperty();
    if (!prop?.id) return;
    this.chemistryService.deleteMolecularProperty(prop.id).subscribe({
      next: () => {
        this.showDeleteProperty.set(false);
        this.selectedProperty.set(null);
        const mol = this.molecule();
        if (mol?.id) this.loadProperties(mol.id);
      },
      error: (err) =>
        this.error.set(err?.message || 'Failed to delete property'),
    });
  }

  updatePropertyType(value: string): void {
    this.propertyForm.set({ ...this.propertyForm(), property_type: value });
  }

  updatePropertyValue(value: string): void {
    this.propertyForm.set({ ...this.propertyForm(), value });
  }

  updatePropertyUnits(value: string): void {
    this.propertyForm.set({ ...this.propertyForm(), units: value });
  }

  updatePropertyMethod(value: string): void {
    this.propertyForm.set({ ...this.propertyForm(), method: value });
  }

  onPropertyAction(event: { action: string; row: any }): void {
    const { action, row } = event;
    if (action === 'edit') {
      this.openEditProperty(row);
    } else if (action === 'delete') {
      this.openDeleteProperty(row);
    }
  }
}
