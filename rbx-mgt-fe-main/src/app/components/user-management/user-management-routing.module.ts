import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

const routes: Routes = [
  {
    path:'maintain_users',
    loadComponent: () => import('./maintain-user-grid/maintain-user-grid.component').then(c => c.MaintainUserGridComponent),
    data: { breadcrumb: 'Maintain Users' }
  },
  {
    path:'user_registration',
    loadComponent: () => import('./user-registration/user-registration.component').then(c => c.UserRegistrationComponent),
    data: { breadcrumb: 'User Registration' }
  },
  {
    path:'edit_user/:id',
    loadComponent: () => import('./user-registration/user-registration.component').then(c => c.UserRegistrationComponent),
    data: { breadcrumb: 'Edit User' }
  },
  {
    path:'maintain_roles',
    loadComponent: () => import('./maintain-role/maintain-role.component').then(c => c.MaintainRoleComponent),
    data: { breadcrumb: 'Maintain Roles' }
  },
  {
    path:'assign_roles',
    loadComponent: () => import('./assign-role/assign-role.component').then(c => c.AssignRoleComponent),
    data: { breadcrumb: 'Assign Roles' }
  },
  {
    path:'view_user',
    loadComponent: () => import('./view-user/view-user.component').then(c => c.ViewUserComponent),
    data: { breadcrumb: 'View User' }
  },
  // {
  //   path:'master_data',
  //   loadComponent: () => import('./maintain-user-grid/maintain-user-grid.component').then(c => c.MaintainUserGridComponent)
  // },
  
];
@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class UserManagementRoutingModule { }
