import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import { PermissionsService } from '../api/api/permissions.service';
import { RolesService } from '../api/api/roles.service';
import { UsersService as ApiUsersService } from '../api/api/users.service';

/**
 * Application service for users, roles, and permissions.
 */
@Injectable({ providedIn: 'root' })
export class UsersAppService {
  private readonly usersApi = inject(ApiUsersService);
  private readonly rolesApi = inject(RolesService);
  private readonly permissionsApi = inject(PermissionsService);

  // ========== Users ==========
  listUsers(params?: any): Observable<any[]> {
    return this.usersApi
      .usersUsersList(params?.limit, params?.offset)
      .pipe(
        map((result) =>
          Array.isArray(result) ? result : (result as any).results ?? []
        )
      );
  }

  getUser(id: number): Observable<any> {
    return this.usersApi.usersUsersRetrieve(id);
  }

  getCurrentUser(): Observable<any> {
    return this.usersApi.usersUsersMeRetrieve();
  }

  createUser(data: any): Observable<any> {
    return this.usersApi.usersUsersCreate(data);
  }

  updateUser(id: number, data: any): Observable<any> {
    return this.usersApi.usersUsersPartialUpdate(id, data);
  }

  deleteUser(id: number): Observable<void> {
    return this.usersApi.usersUsersDestroy(id);
  }

  activateUser(id: number): Observable<any> {
    return (this.usersApi as any).usersUsersActivateCreate?.(id, {});
  }

  deactivateUser(id: number): Observable<any> {
    return (this.usersApi as any).usersUsersDeactivateCreate?.(id, {});
  }

  adminChangePassword(id: number, data: { password: string }): Observable<any> {
    return (this.usersApi as any).usersUsersAdminChangePasswordCreate?.(
      id,
      data
    );
  }

  adminUpdate(id: number, data: any): Observable<any> {
    return (this.usersApi as any).usersUsersAdminUpdatePartialUpdate?.(
      id,
      data
    );
  }

  getUserPermissions(id: number): Observable<any[]> {
    return (this.usersApi as any)
      .usersUsersPermissionsRetrieve?.(id)
      .pipe(map((r: any) => (Array.isArray(r) ? r : r?.results ?? [])));
  }

  getUserResources(id: number): Observable<any[]> {
    return (this.usersApi as any)
      .usersUsersResourcesRetrieve?.(id)
      .pipe(map((r: any) => (Array.isArray(r) ? r : r?.results ?? [])));
  }

  changePassword(data: {
    old_password: string;
    new_password: string;
  }): Observable<any> {
    return (this.usersApi as any).usersUsersChangePasswordCreate?.(data);
  }

  meUpdate(data: any): Observable<any> {
    return (this.usersApi as any).usersUsersMeUpdatePartialUpdate?.(data);
  }

  requestPasswordReset(data: { email: string }): Observable<any> {
    return (this.usersApi as any).usersUsersRequestPasswordResetCreate?.(data);
  }

  resetPassword(data: { token: string; password: string }): Observable<any> {
    return (this.usersApi as any).usersUsersResetPasswordCreate?.(data);
  }

  sendVerificationEmail(data: { email: string }): Observable<any> {
    return (this.usersApi as any).usersUsersSendVerificationEmailCreate?.(data);
  }

  verifyEmail(data: { token: string }): Observable<any> {
    return (this.usersApi as any).usersUsersVerifyEmailCreate?.(data);
  }

  // ========== Roles ==========
  listRoles(params?: any): Observable<any[]> {
    return this.rolesApi
      .usersRolesList(params?.limit, params?.offset)
      .pipe(
        map((result) =>
          Array.isArray(result) ? result : (result as any).results ?? []
        )
      );
  }

  getRole(id: number): Observable<any> {
    return this.rolesApi.usersRolesRetrieve(id);
  }

  createRole(data: any): Observable<any> {
    return this.rolesApi.usersRolesCreate(data);
  }

  updateRole(id: number, data: any): Observable<any> {
    return this.rolesApi.usersRolesPartialUpdate(id, data);
  }

  deleteRole(id: number): Observable<void> {
    return this.rolesApi.usersRolesDestroy(id);
  }

  // ========== Permissions ==========
  listPermissions(params?: any): Observable<any[]> {
    return this.permissionsApi
      .usersPermissionsList(params?.limit, params?.offset)
      .pipe(
        map((result) =>
          Array.isArray(result) ? result : (result as any).results ?? []
        )
      );
  }

  getPermission(id: number): Observable<any> {
    return this.permissionsApi.usersPermissionsRetrieve(id);
  }
}
