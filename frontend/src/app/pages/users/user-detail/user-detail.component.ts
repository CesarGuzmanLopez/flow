import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { UsersAppService } from '../../../services/users-app.service';
import { ConfirmDialogComponent } from '../../../shared/components/confirm-dialog/confirm-dialog.component';
import { ModalComponent } from '../../../shared/components/modal/modal.component';

@Component({
  selector: 'app-user-detail',
  standalone: true,
  imports: [CommonModule, FormsModule, ConfirmDialogComponent, ModalComponent],
  templateUrl: './user-detail.component.html',
  styleUrls: ['./user-detail.component.scss'],
})
export class UserDetailComponent implements OnInit {
  private readonly users = inject(UsersAppService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  user = signal<any | null>(null);
  roles = signal<any[]>([]);
  permissions = signal<any[]>([]);
  loading = signal(false);
  error = signal<string | null>(null);
  showDeleteModal = signal(false);
  isEditing = signal(false);

  // Extra actions modals
  showChangePassword = signal(false);
  showActivate = signal(false);
  showDeactivate = signal(false);
  changePasswordForm = signal({ password: '' });

  editForm = signal({
    username: '',
    email: '',
    first_name: '',
    last_name: '',
    is_active: true,
    is_staff: false,
  });

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.loadUser(+id);
    }
  }

  loadUser(id: number): void {
    this.loading.set(true);
    this.users.getUser(id).subscribe({
      next: (data: any) => {
        this.user.set(data);
        this.editForm.set({
          username: data.username,
          email: data.email,
          first_name: data.first_name,
          last_name: data.last_name,
          is_active: data.is_active,
          is_staff: data.is_staff,
        });
        this.loading.set(false);
      },
      error: (err: any) => {
        this.error.set(err?.message || 'Error cargando usuario');
        this.loading.set(false);
      },
    });
  }

  toggleEdit(): void {
    this.isEditing.set(!this.isEditing());
  }

  saveChanges(): void {
    const u = this.user();
    if (!u?.id) return;
    this.loading.set(true);
    this.users.updateUser(u.id, this.editForm()).subscribe({
      next: () => {
        this.loading.set(false);
        this.isEditing.set(false);
        this.loadUser(u.id);
      },
      error: (err: any) => {
        this.error.set(err?.message || 'Error actualizando usuario');
        this.loading.set(false);
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
    const u = this.user();
    if (!u?.id) return;
    this.users.deleteUser(u.id).subscribe({
      next: () => this.router.navigate(['/users']),
      error: (err: any) =>
        this.error.set(err?.message || 'Error eliminando usuario'),
    });
  }

  // Extra actions
  openChangePassword(): void {
    this.changePasswordForm.set({ password: '' });
    this.showChangePassword.set(true);
  }

  submitChangePassword(): void {
    const u = this.user();
    if (!u?.id || !this.changePasswordForm().password) return;
    this.users
      .adminChangePassword(u.id, {
        password: this.changePasswordForm().password,
      })
      .subscribe({
        next: () => this.showChangePassword.set(false),
        error: (err: any) =>
          this.error.set(err?.message || 'Error al cambiar contraseña'),
      });
  }

  openActivate(): void {
    this.showActivate.set(true);
  }

  openDeactivate(): void {
    this.showDeactivate.set(true);
  }

  confirmActivate(): void {
    const u = this.user();
    if (!u?.id) return;
    this.users.activateUser(u.id).subscribe({
      next: () => {
        this.showActivate.set(false);
        this.loadUser(u.id);
      },
      error: (err: any) =>
        this.error.set(err?.message || 'Error activando usuario'),
    });
  }

  confirmDeactivate(): void {
    const u = this.user();
    if (!u?.id) return;
    this.users.deactivateUser(u.id).subscribe({
      next: () => {
        this.showDeactivate.set(false);
        this.loadUser(u.id);
      },
      error: (err: any) =>
        this.error.set(err?.message || 'Error desactivando usuario'),
    });
  }

  goBack(): void {
    this.router.navigate(['/users']);
  }

  // Template helpers to avoid complex expressions in templates
  onEditInput(
    field: keyof typeof this.editForm extends infer T ? any : any,
    value: string
  ): void {
    const cur = this.editForm();
    this.editForm.set({ ...cur, [field]: value } as any);
  }

  onToggle(field: 'is_active' | 'is_staff'): void {
    const cur = this.editForm();
    this.editForm.set({ ...cur, [field]: !cur[field] } as any);
  }
}
