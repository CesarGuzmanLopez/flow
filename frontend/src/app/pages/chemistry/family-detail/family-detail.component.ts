import { CommonModule } from '@angular/common';
import { Component, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ChemistryAppService } from '../../../services/chemistry-app.service';
import { FlowsAppService } from '../../../services/flows.service';
import { ConfirmDialogComponent } from '../../../shared/components/confirm-dialog/confirm-dialog.component';
import {
  DataTableComponent,
  TableColumn,
} from '../../../shared/components/data-table/data-table.component';
import { ModalComponent } from '../../../shared/components/modal/modal.component';

@Component({
  selector: 'app-family-detail',
  standalone: true,
  imports: [
    CommonModule,
    DataTableComponent,
    ModalComponent,
    ConfirmDialogComponent,
    FormsModule,
  ],
  templateUrl: './family-detail.component.html',
  styleUrls: ['./family-detail.component.scss'],
})
export class FamilyDetailComponent implements OnInit {
  family = signal<any>(null);
  members = signal<any[]>([]);
  properties = signal<any[]>([]);
  loading = signal(true);
  error = signal<string | null>(null);
  showDeleteModal = signal(false);
  // Members modals
  showAddMember = signal(false);
  showRemoveMember = signal(false);
  selectedMember = signal<any | null>(null);
  addMemberForm = signal<{ molecule_id: number | null }>({ molecule_id: null });

  membersColumns: TableColumn[] = [
    { key: 'molecule_id', label: 'Molecule ID', type: 'number' },
    { key: 'molecule_name', label: 'Name', type: 'text' },
    { key: 'smiles', label: 'SMILES', type: 'text' },
    { key: 'added_at', label: 'Added', type: 'date' },
  ];

  propertiesColumns: TableColumn[] = [
    { key: 'name', label: 'Property', type: 'text' },
    { key: 'aggregation', label: 'Aggregation', type: 'text' },
    { key: 'value', label: 'Value', type: 'text' },
    { key: 'unit', label: 'Unit', type: 'text' },
    { key: 'calculated_at', label: 'Calculated', type: 'date' },
  ];

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private chemistryService: ChemistryAppService,
    private flowsService: FlowsAppService
  ) {}

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.loadFamily(+id);
      this.loadMembers(+id);
      this.loadProperties(+id);
    }
  }

  loadFamily(id: number): void {
    this.loading.set(true);
    this.error.set(null);

    this.chemistryService.getFamily(id).subscribe({
      next: (data) => {
        this.family.set(data);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err.message || 'Failed to load family');
        this.loading.set(false);
      },
    });
  }

  loadMembers(familyId: number): void {
    this.chemistryService.listFamilyMembers().subscribe({
      next: (data) => {
        // Filter members by family ID (assuming API returns all members)
        const filteredMembers = (data || []).filter(
          (m: any) => m.family_id === familyId
        );
        this.members.set(filteredMembers);
      },
      error: (err) => {
        console.error('Failed to load members:', err);
      },
    });
  }

  loadProperties(familyId: number): void {
    this.chemistryService.listFamilyProperties().subscribe({
      next: (data) => {
        // Filter properties by family ID
        const filteredProps = (data || []).filter(
          (p: any) => p.family_id === familyId
        );
        this.properties.set(filteredProps);
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
    const fam = this.family();
    if (fam?.id) {
      this.chemistryService.deleteFamily(fam.id).subscribe({
        next: () => {
          this.router.navigate(['/chemistry/families']);
        },
        error: (err) => {
          this.error.set(err.message || 'Failed to delete family');
          this.showDeleteModal.set(false);
        },
      });
    }
  }

  // Members actions
  openAddMember(): void {
    this.addMemberForm.set({ molecule_id: null });
    this.showAddMember.set(true);
  }

  addMember(): void {
    const fam = this.family();
    const molecule_id = this.addMemberForm().molecule_id;
    if (!fam?.id || !molecule_id) return;
    const payload: any = { family_id: fam.id, molecule_id };
    this.chemistryService.createFamilyMember(payload).subscribe({
      next: () => {
        this.showAddMember.set(false);
        this.loadMembers(fam.id);
      },
      error: (err) =>
        this.error.set(err?.message || 'No se pudo añadir la molécula'),
    });
  }

  openRemoveMember(member: any): void {
    this.selectedMember.set(member);
    this.showRemoveMember.set(true);
  }

  removeMember(): void {
    const fam = this.family();
    const m = this.selectedMember();
    if (!fam?.id || !m?.id) return;
    this.chemistryService.deleteFamilyMember(m.id).subscribe({
      next: () => {
        this.showRemoveMember.set(false);
        this.selectedMember.set(null);
        this.loadMembers(fam.id);
      },
      error: (err) =>
        this.error.set(err?.message || 'No se pudo eliminar la molécula'),
    });
  }

  goBack(): void {
    this.router.navigate(['/chemistry/families']);
  }

  // Actions using flows step execution endpoints
  computeAdmetsa(): void {
    const fam = this.family();
    if (!fam?.id) return;
    const payload = {
      step_type: 'generate_admetsa',
      params: { family_id: fam.id },
    };
    this.flowsService.executeStep(payload).subscribe({
      next: () => this.loadProperties(fam.id),
      error: (err) => {
        console.error('Failed to compute ADMETSA', err);
        this.error.set('No se pudo calcular ADMETSA');
      },
    });
  }

  computeAggregates(): void {
    const fam = this.family();
    if (!fam?.id) return;
    const payload = {
      step_type: 'generate_admetsa_family_aggregates',
      params: { family_id: fam.id },
    };
    this.flowsService.executeStep(payload).subscribe({
      next: () => this.loadProperties(fam.id),
      error: (err) => {
        console.error('Failed to compute aggregates', err);
        this.error.set('No se pudo calcular agregados');
      },
    });
  }
}
