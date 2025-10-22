import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ChemistryAppService } from '../../services/chemistry-app.service';
import { FlowsAppService } from '../../services/flows.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss'],
})
export class DashboardComponent implements OnInit {
  private readonly flows = inject(FlowsAppService);
  private readonly chem = inject(ChemistryAppService);

  loading = signal(true);
  error = signal<string | null>(null);

  flowCount = signal(0);
  familyCount = signal(0);
  moleculeCount = signal(0);

  recentFlows = signal<any[]>([]);

  ngOnInit(): void {
    this.refresh();
  }

  refresh(): void {
    this.loading.set(true);
    this.error.set(null);

    // Load flows summary
    this.flows
      .listFlows()
      .subscribe({
        next: (fs) => {
          this.flowCount.set(fs.length);
          this.recentFlows.set(fs.slice(0, 5));
          this.loading.set(false);
        },
        error: (err) => {
          this.error.set(err?.message || 'Error cargando flujos');
          this.loading.set(false);
        },
      });

    // Families
    this.chem.listFamilies({ limit: 1_000 }).subscribe({
      next: (list) => this.familyCount.set(list.length),
      error: () => {},
    });

    // Molecules
    this.chem.listMolecules({ limit: 1_000 }).subscribe({
      next: (list) => this.moleculeCount.set(list.length),
      error: () => {},
    });
  }
}
