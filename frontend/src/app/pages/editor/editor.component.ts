import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { FlowsAppService } from '../../services/flows.service';
import { JsonInputComponent } from '../../shared/components/json-input/json-input.component';

@Component({
  selector: 'app-editor',
  standalone: true,
  imports: [CommonModule, JsonInputComponent],
  templateUrl: './editor.component.html',
  styleUrls: ['./editor.component.scss'],
})
export class EditorComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly flows = inject(FlowsAppService);

  flowId = signal<number | null>(null);
  branches = signal<any[]>([]);
  selectedBranchId = signal<number | null>(null);
  pathNodes = signal<any[]>([]);
  loading = signal(false);
  error = signal<string | null>(null);

  // Append step form
  stepType = signal('create_reference_family');
  stepParams: any = { mode: 'new', name: 'Fam', smiles_list: ['CCO'] };

  ngOnInit(): void {
    const idParam = this.route.snapshot.paramMap.get('id');
    if (idParam) {
      this.flowId.set(+idParam);
    }
    this.loadBranches();
  }

  loadBranches(): void {
    this.loading.set(true);
    this.error.set(null);
    this.flows.listBranches().subscribe({
      next: (data) => {
        const fid = this.flowId();
        const list = (Array.isArray(data) ? data : (data as any).results) || [];
        const filtered = fid
          ? list.filter((b: any) => b.flow_id === fid || b.flow === fid)
          : list;
        this.branches.set(filtered);
        if (filtered.length && !this.selectedBranchId()) {
          this.selectedBranchId.set(filtered[0].id);
          this.loadPath();
        }
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err?.message || 'Error cargando ramas');
        this.loading.set(false);
      },
    });
  }

  loadPath(): void {
    const bid = this.selectedBranchId();
    if (!bid) return;
    this.flows.getBranchPath(bid).subscribe({
      next: (path) => {
        const nodes = (path as any)?.nodes || (Array.isArray(path) ? path : []);
        this.pathNodes.set(nodes);
      },
      error: (err) => this.error.set(err?.message || 'Error cargando camino'),
    });
  }

  onSelectBranch(bid: number): void {
    this.selectedBranchId.set(bid);
    this.loadPath();
  }

  appendStep(): void {
    const bid = this.selectedBranchId();
    if (!bid) return;
    const payload = {
      step_type: this.stepType(),
      params: this.stepParams,
    };
    this.loading.set(true);
    this.flows.addStepToBranch(bid, payload).subscribe({
      next: () => {
        this.loading.set(false);
        this.loadPath();
      },
      error: (err) => {
        this.error.set(err?.message || 'Error agregando step');
        this.loading.set(false);
      },
    });
  }
}
