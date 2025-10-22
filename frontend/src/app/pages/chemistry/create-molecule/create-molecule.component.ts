import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ChemistryAppService } from '../../../services/chemistry-app.service';
import { JsonViewerComponent } from '../../../shared/components/json-viewer/json-viewer.component';

@Component({
  selector: 'app-create-molecule',
  standalone: true,
  imports: [CommonModule, FormsModule, JsonViewerComponent],
  templateUrl: './create-molecule.component.html',
  styleUrls: ['./create-molecule.component.scss'],
})
export class CreateMoleculeComponent implements OnInit {
  private readonly chem = inject(ChemistryAppService);
  private readonly router = inject(Router);

  formData = signal({
    smiles: '',
    name: '',
  });
  loading = signal(false);
  error = signal<string | null>(null);
  success = signal(false);
  createdMolecule = signal<any | null>(null);

  ngOnInit(): void {}

  submit(): void {
    const form = this.formData();
    if (!form.smiles) {
      this.error.set('SMILES es requerido');
      return;
    }

    this.loading.set(true);
    this.error.set(null);

    this.chem
      .createMolecule({ smiles: form.smiles, name: form.name } as any)
      .subscribe({
        next: (mol: any) => {
          this.loading.set(false);
          this.success.set(true);
          this.createdMolecule.set(mol);
          setTimeout(() => {
            this.router.navigate(['/chemistry/molecules', mol.id]);
          }, 2000);
        },
        error: (err: any) => {
          this.loading.set(false);
          this.error.set(err?.message || 'Error creando molécula');
        },
      });
  }

  goBack(): void {
    this.router.navigate(['/chemistry/molecules']);
  }

  // Helper for template-safe updates (avoids complex expressions in template)
  onFormInput(field: 'smiles' | 'name', value: string): void {
    const current = this.formData();
    this.formData.set({ ...current, [field]: value });
  }
}
