import { CommonModule } from '@angular/common';
import { Component, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { UsersAppService } from '../../../services/users-app.service';
import {
  DataTableComponent,
  TableColumn,
} from '../../../shared/components/data-table/data-table.component';
import { ModalComponent } from '../../../shared/components/modal/modal.component';

@Component({
  selector: 'app-roles-list',
  standalone: true,
  imports: [CommonModule, FormsModule, DataTableComponent, ModalComponent],
  templateUrl: './roles-list.component.html',
  styleUrls: ['./roles-list.component.scss'],
})
export class RolesListComponent implements OnInit {
  roles = signal<any[]>([]);
  permissions = signal<any[]>([]);
  loading = signal(false);
  error = signal<string | null>(null);
  showCreateModal = signal(false);
  newRole = signal({
    name: '',
    description: '',
    permissions: [] as number[],
  });

  columns: TableColumn[] = [
    { key: 'id', label: 'ID', type: 'number' },
    { key: 'name', label: 'Name', type: 'text' },
    { key: 'description', label: 'Description', type: 'text' },
    { key: 'created_at', label: 'Created', type: 'date' },
  ];

  constructor(private router: Router, private usersService: UsersAppService) {}

  ngOnInit(): void {
    this.loadRoles();
    this.loadPermissions();
  }

  loadRoles(): void {
    this.loading.set(true);
    this.error.set(null);

    this.usersService.listRoles().subscribe({
      next: (data) => {
        this.roles.set(data);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err.message || 'Failed to load roles');
        this.loading.set(false);
      },
    });
  }

  loadPermissions(): void {
    this.usersService.listPermissions().subscribe({
      next: (data) => {
        this.permissions.set(data);
      },
      error: (err) => {
        console.error('Failed to load permissions:', err);
      },
    });
  }

  onRowClick(role: any): void {
    this.router.navigate(['/roles', role.id]);
  }

  openCreateModal(): void {
    this.showCreateModal.set(true);
  }

  closeCreateModal(): void {
    this.showCreateModal.set(false);
    this.resetNewRole();
  }

  resetNewRole(): void {
    this.newRole.set({
      name: '',
      description: '',
      permissions: [],
    });
  }

  togglePermission(permissionId: number): void {
    const current = this.newRole();
    const permissions = current.permissions.includes(permissionId)
      ? current.permissions.filter((id) => id !== permissionId)
      : [...current.permissions, permissionId];

    this.newRole.set({ ...current, permissions });
  }

  isPermissionSelected(permissionId: number): boolean {
    return this.newRole().permissions.includes(permissionId);
  }

  createRole(): void {
    const role = this.newRole();
    if (!role.name) {
      this.error.set('Role name is required');
      return;
    }

    this.usersService.createRole(role as any).subscribe({
      next: () => {
        this.closeCreateModal();
        this.loadRoles();
      },
      error: (err) => {
        this.error.set(err.message || 'Failed to create role');
      },
    });
  }
}
