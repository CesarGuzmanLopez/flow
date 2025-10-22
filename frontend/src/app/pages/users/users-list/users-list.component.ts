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
  selector: 'app-users-list',
  standalone: true,
  imports: [CommonModule, FormsModule, DataTableComponent, ModalComponent],
  templateUrl: './users-list.component.html',
  styleUrls: ['./users-list.component.scss'],
})
export class UsersListComponent implements OnInit {
  users = signal<any[]>([]);
  loading = signal(false);
  error = signal<string | null>(null);
  showCreateModal = signal(false);
  newUser = signal({
    username: '',
    email: '',
    password: '',
    first_name: '',
    last_name: '',
  });

  columns: TableColumn[] = [
    { key: 'id', label: 'ID', type: 'number' },
    { key: 'username', label: 'Username', type: 'text' },
    { key: 'email', label: 'Email', type: 'text' },
    { key: 'first_name', label: 'First Name', type: 'text' },
    { key: 'last_name', label: 'Last Name', type: 'text' },
    { key: 'is_active', label: 'Active', type: 'badge' },
    { key: 'is_staff', label: 'Staff', type: 'badge' },
    { key: 'date_joined', label: 'Joined', type: 'date' },
  ];

  constructor(private router: Router, private usersService: UsersAppService) {}

  ngOnInit(): void {
    this.loadUsers();
  }

  loadUsers(): void {
    this.loading.set(true);
    this.error.set(null);

    this.usersService.listUsers().subscribe({
      next: (data) => {
        this.users.set(data);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err.message || 'Failed to load users');
        this.loading.set(false);
      },
    });
  }

  onRowClick(user: any): void {
    this.router.navigate(['/users', user.id]);
  }

  openCreateModal(): void {
    this.showCreateModal.set(true);
  }

  closeCreateModal(): void {
    this.showCreateModal.set(false);
    this.resetNewUser();
  }

  resetNewUser(): void {
    this.newUser.set({
      username: '',
      email: '',
      password: '',
      first_name: '',
      last_name: '',
    });
  }

  createUser(): void {
    const user = this.newUser();
    if (!user.username || !user.email || !user.password) {
      this.error.set('Username, email, and password are required');
      return;
    }

    this.usersService.createUser(user as any).subscribe({
      next: () => {
        this.closeCreateModal();
        this.loadUsers();
      },
      error: (err) => {
        this.error.set(err.message || 'Failed to create user');
      },
    });
  }
}
