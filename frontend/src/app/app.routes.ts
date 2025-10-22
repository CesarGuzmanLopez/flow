import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: '/dashboard', pathMatch: 'full' },
  {
    path: 'login',
    loadComponent: () =>
      import('./pages/login/login.component').then((m) => m.LoginComponent),
  },
  {
    path: 'dashboard',
    loadComponent: () =>
      import('./pages/dashboard/dashboard.component').then(
        (m) => m.DashboardComponent
      ),
    canActivate: [authGuard],
  },
  {
    path: 'editor/:id',
    loadComponent: () =>
      import('./pages/editor/editor.component').then((m) => m.EditorComponent),
    canActivate: [authGuard],
  },
  {
    path: 'editor/new',
    loadComponent: () =>
      import('./pages/editor/editor.component').then((m) => m.EditorComponent),
    canActivate: [authGuard],
  },
  // Flows feature module (lazy-loaded)
  {
    path: 'flows',
    canActivate: [authGuard],
    children: [
      {
        path: '',
        loadComponent: () =>
          import('./pages/flows/flows-list.component').then(
            (m) => m.FlowsListComponent
          ),
      },
      {
        path: ':id',
        loadComponent: () =>
          import('./pages/flows/flow-detail/flow-detail.component').then(
            (m) => m.FlowDetailComponent
          ),
      },
      {
        path: 'executions',
        loadComponent: () =>
          import('./pages/flows/executions/executions.component').then(
            (m) => m.ExecutionsComponent
          ),
      },
      {
        path: 'artifacts',
        loadComponent: () =>
          import('./pages/flows/artifacts/artifacts.component').then(
            (m) => m.ArtifactsComponent
          ),
      },
      {
        path: 'step-catalog',
        loadComponent: () =>
          import('./pages/flows/step-catalog/step-catalog.component').then(
            (m) => m.StepCatalogComponent
          ),
      },
      {
        path: 'steps',
        loadComponent: () =>
          import('./pages/flows/steps-list/steps-list.component').then(
            (m) => m.StepsListComponent
          ),
      },
      {
        path: 'branch-management',
        loadComponent: () =>
          import(
            './pages/flows/branch-management/branch-management.component'
          ).then((m) => m.BranchManagementComponent),
      },
      {
        path: 'nodes',
        loadComponent: () =>
          import('./pages/flows/nodes-viewer/nodes-viewer.component').then(
            (m) => m.NodesViewerComponent
          ),
      },
    ],
  },
  // Chemistry feature module (lazy-loaded)
  {
    path: 'chemistry',
    canActivate: [authGuard],
    children: [
      {
        path: 'molecules',
        loadComponent: () =>
          import(
            './pages/chemistry/molecules-list/molecules-list.component'
          ).then((m) => m.MoleculesListComponent),
      },
      {
        path: 'molecules/create',
        loadComponent: () =>
          import(
            './pages/chemistry/create-molecule/create-molecule.component'
          ).then((m) => m.CreateMoleculeComponent),
      },
      {
        path: 'molecules/:id',
        loadComponent: () =>
          import(
            './pages/chemistry/molecule-detail/molecule-detail.component'
          ).then((m) => m.MoleculeDetailComponent),
      },
      {
        path: 'families',
        loadComponent: () =>
          import(
            './pages/chemistry/families-list/families-list.component'
          ).then((m) => m.FamiliesListComponent),
      },
      {
        path: 'families/create',
        loadComponent: () =>
          import(
            './pages/chemistry/create-family/create-family.component'
          ).then((m) => m.CreateFamilyComponent),
      },
      {
        path: 'families/:id',
        loadComponent: () =>
          import(
            './pages/chemistry/family-detail/family-detail.component'
          ).then((m) => m.FamilyDetailComponent),
      },
    ],
  },
  // Users feature module (lazy-loaded)
  {
    path: 'users',
    canActivate: [authGuard],
    children: [
      {
        path: '',
        loadComponent: () =>
          import('./pages/users/users-list/users-list.component').then(
            (m) => m.UsersListComponent
          ),
      },
      {
        path: ':id',
        loadComponent: () =>
          import('./pages/users/user-detail/user-detail.component').then(
            (m) => m.UserDetailComponent
          ),
      },
      {
        path: 'roles',
        loadComponent: () =>
          import('./pages/users/roles-list/roles-list.component').then(
            (m) => m.RolesListComponent
          ),
      },
    ],
  },
  // Notifications (lazy-loaded)
  {
    path: 'notifications',
    loadComponent: () =>
      import('./pages/notifications/notifications.component').then(
        (m) => m.NotificationsComponent
      ),
    canActivate: [authGuard],
  },
  { path: '**', redirectTo: '/dashboard' },
];

