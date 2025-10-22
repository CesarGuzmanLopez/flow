import { CommonModule, NgForOf, NgIf } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { FlowsAppService } from '../../../services/flows.service';
import { JsonViewerComponent } from '../../../shared/components/json-viewer/json-viewer.component';
import { ModalComponent } from '../../../shared/components/modal/modal.component';

@Component({
  selector: 'app-nodes-viewer',
  standalone: true,
  imports: [
    CommonModule,
    NgIf,
    NgForOf,
    FormsModule,
    ReactiveFormsModule,
    RouterModule,
    ModalComponent,
    JsonViewerComponent,
  ],
  templateUrl: './nodes-viewer.component.html',
  styleUrls: ['./nodes-viewer.component.scss'],
})
export class NodesViewerComponent implements OnInit {
  private flows = inject(FlowsAppService);

  // State
  nodes = signal<any[]>([]);
  loading = signal(false);
  error = signal<string | null>(null);
  expandedNodeIds = signal<Set<number>>(new Set());
  selectedNode = signal<any | null>(null);
  showNodeModal = signal(false);

  ngOnInit(): void {
    this.loadNodes();
  }

  // Exposed for template retry
  loadNodes(): void {
    this.loading.set(true);
    this.error.set(null);

    this.flows.listNodes().subscribe({
      next: (nodes) => {
        this.nodes.set(nodes);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set('Error cargando nodos');
        this.loading.set(false);
        console.error(err);
      },
    });
  }

  toggleNode(nodeId: number): void {
    const expanded = new Set(this.expandedNodeIds());
    if (expanded.has(nodeId)) {
      expanded.delete(nodeId);
    } else {
      expanded.add(nodeId);
    }
    this.expandedNodeIds.set(expanded);
  }

  isNodeExpanded(nodeId: number): boolean {
    return this.expandedNodeIds().has(nodeId);
  }

  getRootNodes(): any[] {
    return this.nodes().filter((n) => !n.parent_id);
  }

  getChildNodes(nodeId: number): any[] {
    return this.nodes().filter((n) => n.parent_id === nodeId);
  }

  getNodeLevel(nodeId: number, currentLevel: number = 0): number {
    const node = this.nodes().find((n) => n.id === nodeId);
    if (!node?.parent_id) return currentLevel;
    return this.getNodeLevel(node.parent_id, currentLevel + 1);
  }

  openNode(nodeId: number): void {
    this.flows.getNode(nodeId).subscribe({
      next: (node) => {
        this.selectedNode.set(
          node || this.nodes().find((n) => n.id === nodeId)
        );
        this.showNodeModal.set(true);
      },
      error: () => {
        this.selectedNode.set(
          this.nodes().find((n) => n.id === nodeId) || null
        );
        this.showNodeModal.set(true);
      },
    });
  }

  closeNodeModal(): void {
    this.showNodeModal.set(false);
    this.selectedNode.set(null);
  }
}
