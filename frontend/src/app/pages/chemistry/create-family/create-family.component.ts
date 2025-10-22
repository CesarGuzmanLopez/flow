import { CommonModule } from '@angular/common';
import { Component, inject, OnDestroy, OnInit, signal } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';
import { ChemistryAppService } from '../../../services/chemistry-app.service';

@Component({
  selector: 'app-create-family',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule, RouterModule],
  templateUrl: './create-family.component.html',
  styleUrls: ['./create-family.component.scss'],
})
export class CreateFamilyComponent implements OnInit, OnDestroy {
  private chemistry = inject(ChemistryAppService);
  private router = inject(Router);
  private destroy$ = new Subject<void>();

  // Form mode
  mode = signal<'new' | 'existing' | 'reference'>('new');

  // State
  loading = signal(false);
  error = signal<string | null>(null);
  success = signal(false);
  createdFamilyId = signal<number | null>(null);

  // New Family Form
  familyName = signal('');
  familyDescription = signal('');
  referenceMoleculeSMILES = signal('');

  // Existing Family Mode
  selectedFamilyId = signal<number | null>(null);
  families = signal<any[]>([]);

  // Reference Molecule Mode
  referenceMoleculeId = signal<number | null>(null);
  molecules = signal<any[]>([]);

  // Results
  createdFamily = signal<any | null>(null);
  aggregates = signal<any[]>([]);

  ngOnInit(): void {
    if (this.mode() === 'existing') {
      this.loadFamilies();
    } else if (this.mode() === 'reference') {
      this.loadMolecules();
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  // Exposed for template retry button
  loadFamilies(): void {
    this.chemistry
      .listFamilies()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (families) => {
          this.families.set(families);
        },
        error: (err) => {
          this.error.set('Error cargando familias');
          console.error(err);
        },
      });
  }

  // Exposed for template retry button
  loadMolecules(): void {
    this.chemistry
      .listMolecules()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (molecules) => {
          this.molecules.set(molecules);
        },
        error: (err) => {
          this.error.set('Error cargando moléculas');
          console.error(err);
        },
      });
  }

  onSelectExistingFamily(value: string | number | null): void {
    const id = value === null || value === 'null' ? null : Number(value);
    this.selectedFamilyId.set(id);
  }

  onSelectReferenceMolecule(value: string | number | null): void {
    const id = value === null || value === 'null' ? null : Number(value);
    this.referenceMoleculeId.set(id);
  }

  setMode(newMode: 'new' | 'existing' | 'reference'): void {
    this.mode.set(newMode);
    this.error.set(null);
    this.success.set(false);

    if (newMode === 'existing') {
      this.loadFamilies();
    } else if (newMode === 'reference') {
      this.loadMolecules();
    }
  }

  onCreateNewFamily(): void {
    if (!this.familyName()) {
      this.error.set('El nombre de la familia es requerido');
      return;
    }

    this.loading.set(true);
    this.error.set(null);

    const data: any = {
      name: this.familyName(),
      description: this.familyDescription() || undefined,
    };

    if (this.referenceMoleculeSMILES()) {
      data.reference_molecule_smiles = this.referenceMoleculeSMILES();
    }

    this.chemistry
      .createFamily(data)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (family) => {
          this.loading.set(false);
          this.success.set(true);
          this.createdFamily.set(family);
          this.createdFamilyId.set(family.id);

          // Redirect after 2 seconds
          setTimeout(() => {
            this.router.navigate(['/chemistry/families', family.id]);
          }, 2000);
        },
        error: (err) => {
          this.loading.set(false);
          this.error.set('Error creando familia');
          console.error(err);
        },
      });
  }

  onAddMoleculesToExisting(): void {
    if (!this.selectedFamilyId()) {
      this.error.set('Debes seleccionar una familia existente');
      return;
    }

    this.loading.set(true);
    this.error.set(null);

    // Placeholder for adding molecules to existing family
    // This would call an endpoint to add reference molecules to a family
    console.log('Adding molecules to family:', this.selectedFamilyId());

    this.loading.set(false);
    this.success.set(true);
    this.error.set(null);

    setTimeout(() => {
      this.router.navigate(['/chemistry/families', this.selectedFamilyId()]);
    }, 2000);
  }

  onCreateFromReferenceMolecule(): void {
    if (!this.referenceMoleculeId()) {
      this.error.set('Debes seleccionar una molécula de referencia');
      return;
    }

    this.loading.set(true);
    this.error.set(null);

    // Placeholder for creating family from reference molecule
    // This would call an endpoint to generate a family from a reference
    console.log('Creating family from molecule:', this.referenceMoleculeId());

    this.loading.set(false);
    this.success.set(true);
    this.error.set(null);

    setTimeout(() => {
      this.router.navigate(['/chemistry/families']);
    }, 2000);
  }

  resetForm(): void {
    this.familyName.set('');
    this.familyDescription.set('');
    this.referenceMoleculeSMILES.set('');
    this.selectedFamilyId.set(null);
    this.referenceMoleculeId.set(null);
    this.error.set(null);
    this.success.set(false);
  }
}
