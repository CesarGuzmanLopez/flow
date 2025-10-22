import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Flow } from '../../../api/model/models';
import { FlowsAppService } from '../../../services/flows.service';
import {
  DataTableComponent,
  TableColumn,
} from '../../../shared/components/data-table/data-table.component';

/**
 * Flow detail page: shows flow metadata, versions, branches, and execution history.
 * Allows creating versions, freezing, and executing flows.
 */
@Component({
  selector: 'app-flow-detail',
  standalone: true,
  imports: [CommonModule, DataTableComponent],
  templateUrl: './flow-detail.component.html',
  styleUrls: ['./flow-detail.component.scss'],
})
export class FlowDetailComponent implements OnInit {
  private readonly flowsService = inject(FlowsAppService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  flowId = signal<number | null>(null);
  flow = signal<Flow | null>(null);
  versions = signal<any[]>([]);
  branches = signal<any[]>([]);
  executions = signal<any[]>([]);
  loading = signal(false);
  error = signal<string | null>(null);

  activeTab = signal<'overview' | 'versions' | 'branches' | 'executions'>(
    'overview'
  );

  versionColumns: TableColumn[] = [
    { key: 'version_number', label: 'Versión', type: 'number' },
    { key: 'created_at', label: 'Creada', type: 'date' },
    {
      key: 'is_frozen',
      label: 'Estado',
      type: 'badge',
      badgeClass: (v) => (v ? 'badge completed' : 'badge pending'),
    },
    {
      key: 'actions',
      label: 'Acciones',
      type: 'actions',
      actions: [
        { label: 'Congelar', action: 'freeze' },
        { label: 'Ejecutar', action: 'execute' },
      ],
    },
  ];

  branchColumns: TableColumn[] = [
    { key: 'name', label: 'Nombre', type: 'text' },
    { key: 'created_at', label: 'Creada', type: 'date' },
    {
      key: 'is_default',
      label: 'Por defecto',
      type: 'badge',
      badgeClass: (v) => (v ? 'badge primary' : ''),
    },
  ];

  executionColumns: TableColumn[] = [
    { key: 'id', label: 'ID', type: 'number' },
    { key: 'started_at', label: 'Iniciada', type: 'date' },
    { key: 'finished_at', label: 'Finalizada', type: 'date' },
    {
      key: 'status',
      label: 'Estado',
      type: 'badge',
      badgeClass: (v) => `badge ${v}`,
    },
  ];

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.flowId.set(+id);
      this.loadFlow();
      this.loadVersions();
      this.loadBranches();
      this.loadExecutions();
    }
  }

  loadFlow(): void {
    const id = this.flowId();
    if (!id) return;

    this.loading.set(true);
    this.flowsService.getFlow(id).subscribe({
      next: (flow) => {
        this.flow.set(flow);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err?.message || 'Error al cargar flujo');
        this.loading.set(false);
      },
    });
  }

  loadVersions(): void {
    const id = this.flowId();
    if (!id) return;

    this.flowsService.getVersions(id).subscribe({
      next: (data) => {
        const list = Array.isArray(data) ? data : (data as any).versions ?? [];
        this.versions.set(list);
      },
      error: (err) => console.error('Error loading versions:', err),
    });
  }

  loadBranches(): void {
    const id = this.flowId();
    if (!id) return;

    this.flowsService.listBranches().subscribe({
      next: (data) => {
        // Filter branches by flow ID
        const filtered = (data || []).filter((b: any) => b.flow_id === id);
        this.branches.set(filtered);
      },
      error: (err) => console.error('Error loading branches:', err),
    });
  }

  loadExecutions(): void {
    const id = this.flowId();
    if (!id) return;

    this.flowsService.listExecutions().subscribe({
      next: (data) => {
        // Filter executions by flow ID
        const filtered = (data || []).filter((e: any) => e.flow_id === id);
        this.executions.set(filtered);
      },
      error: (err) => console.error('Error loading executions:', err),
    });
  }

  createVersion(): void {
    const id = this.flowId();
    if (!id) return;

    this.loading.set(true);
    this.flowsService.createVersion(id).subscribe({
      next: () => {
        this.loading.set(false);
        this.loadVersions();
      },
      error: (err) => {
        this.error.set(err?.message || 'Error al crear versión');
        this.loading.set(false);
      },
    });
  }

  createBranch(): void {
    const id = this.flowId();
    if (!id) return;

    const branchName = prompt('Nombre de la nueva rama:');
    if (!branchName?.trim()) return;

    this.loading.set(true);
    this.flowsService.createBranch(id, { name: branchName }).subscribe({
      next: () => {
        this.loading.set(false);
        // Perhaps reload branches if implemented
        alert('Rama creada. Ver gestión de ramas.');
      },
      error: (err) => {
        this.error.set(err?.message || 'Error al crear rama');
        this.loading.set(false);
      },
    });
  }

  freezeVersion(versionId: number): void {
    this.flowsService.freezeVersion(versionId).subscribe({
      next: () => this.loadVersions(),
      error: (err) =>
        this.error.set(err?.message || 'Error al congelar versión'),
    });
  }

  executeVersion(versionId: number): void {
    this.flowsService.executeVersion(versionId).subscribe({
      next: () => {
        alert('Versión ejecutada. Ver página de ejecuciones.');
        this.loadVersions();
      },
      error: (err) =>
        this.error.set(err?.message || 'Error al ejecutar versión'),
    });
  }

  deleteFlow(): void {
    const id = this.flowId();
    if (!id) return;
    if (!confirm('¿Eliminar este flujo permanentemente?')) return;

    this.flowsService.deleteFlow(id).subscribe({
      next: () => this.router.navigate(['/flows']),
      error: (err) => this.error.set(err?.message || 'Error al eliminar flujo'),
    });
  }

  setTab(tab: 'overview' | 'versions' | 'branches' | 'executions') {
    this.activeTab.set(tab);
  }

  onVersionRowClick(version: any) {
    console.log('Version clicked:', version);
  }

  onVersionAction(event: { action: string; row: any }) {
    const { action, row } = event;
    const versionId = row.id;
    if (action === 'freeze') {
      this.freezeVersion(versionId);
    } else if (action === 'execute') {
      this.executeVersion(versionId);
    }
  }

  onBranchRowClick(branch: any) {
    console.log('Branch clicked:', branch);
  }

  onExecutionRowClick(execution: any) {
    console.log('Execution clicked:', execution);
  }
}
