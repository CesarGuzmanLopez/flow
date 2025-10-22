import { CommonModule } from '@angular/common';
import {
  Component,
  inject,
  OnInit,
  signal,
  WritableSignal,
} from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { Flow } from '../../api/model/flow';
import { FlowsAppService } from '../../services/flows.service';
import { JsonInputComponent } from '../../shared/components/json-input/json-input.component';

@Component({
  selector: 'app-flows-list',
  standalone: true,
  imports: [CommonModule, RouterLink, JsonInputComponent],
  templateUrl: './flows-list.component.html',
  styleUrls: ['./flows-list.component.scss'],
})
export class FlowsListComponent implements OnInit {
  private readonly flowsService = inject(FlowsAppService);
  private readonly router = inject(Router);

  flows: WritableSignal<Flow[]> = signal([]);
  loading = signal(false);
  error = signal<string | null>(null);

  // Create from definition form state
  defKey = signal('cadma');
  flowName = signal('CADMA Demo');
  paramsOverride: any = {};

  // Create flow form state
  newFlowName = signal('');
  newFlowDescription = signal('');

  ngOnInit(): void {
    this.refresh();
  }

  refresh(): void {
    this.loading.set(true);
    this.flowsService.listFlows().subscribe({
      next: (list) => {
        this.flows.set(list);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err?.message || 'Error al cargar flujos');
        this.loading.set(false);
      },
    });
  }

  createFromDefinition(): void {
    this.loading.set(true);
    this.flowsService
      .createFromDefinition(this.defKey(), this.flowName(), this.paramsOverride)
      .subscribe({
        next: (flow) => {
          this.loading.set(false);
          const id = flow.id;
          if (id) this.router.navigate(['/flows', id]);
          else this.refresh();
        },
        error: (err) => {
          this.error.set(err?.message || 'Error al crear flujo');
          this.loading.set(false);
        },
      });
  }

  createFlow(): void {
    const data = {
      name: this.newFlowName(),
      description: this.newFlowDescription(),
    };
    this.loading.set(true);
    this.flowsService.createFlow(data).subscribe({
      next: (flow) => {
        this.loading.set(false);
        const id = flow.id;
        if (id) this.router.navigate(['/flows', id]);
        else this.refresh();
      },
      error: (err) => {
        this.error.set(err?.message || 'Error al crear flujo');
        this.loading.set(false);
      },
    });
  }
}
