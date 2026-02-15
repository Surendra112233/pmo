import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AuthGuard } from 'src/app/services/auth.guard';

const routes: Routes = [
  {
    path:'project_tasks',
    loadComponent: () => import('./tasks/project-tasks/project-tasks.component').then(c => c.ProjectTasksComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'add_task',
    loadComponent: () => import('./tasks/add-task/add-task.component').then(c => c.AddTaskComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'edit_task/:id',
    loadComponent: () => import('./tasks/add-task/add-task.component').then(c => c.AddTaskComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'view_task',
    loadComponent: () => import('./tasks/view-task/view-task.component').then(c => c.ViewTaskComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'project_roles',
    loadComponent: () => import('./project-roles/project-roles.component').then(c => c.ProjectRolesComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'add_project_roles',
    loadComponent: () => import('./project-roles/add-project-roles/add-project-roles.component').then(c => c.AddProjectRolesComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'edit_project_roles/:id',
    loadComponent: () => import('./project-roles/add-project-roles/add-project-roles.component').then(c => c.AddProjectRolesComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'view_project_roles',
    loadComponent: () => import('./project-roles/view-project-roles/view-project-roles.component').then(c => c.ViewProjectRolesComponent),
    // data: { roles: ['Manager'] },  
    canActivate: [AuthGuard]
  },
  {
    path:'companies',
    loadComponent: () => import('./it-admin/companies/companies.component').then(c => c.CompaniesComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'add_company',
    loadComponent: () => import('./it-admin/companies/add-company/add-company.component').then(c => c.AddCompanyComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'edit_company/:id',
    loadComponent: () => import('./it-admin/companies/add-company/add-company.component').then(c => c.AddCompanyComponent),
    canActivate: [AuthGuard]
  }, 
  {
    path:'view_company',
    loadComponent: () => import('./it-admin/companies/view-company/view-company.component').then(c => c.ViewCompanyComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'suppliers',
    loadComponent: () => import('./it-admin/suppliers/suppliers.component').then(c => c.SuppliersComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'add_supplier',
    loadComponent: () => import('./it-admin/suppliers/add-supplier/add-supplier.component').then(c => c.AddSupplierComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'edit_supplier/:id',
    loadComponent: () => import('./it-admin/suppliers/add-supplier/add-supplier.component').then(c => c.AddSupplierComponent),
    canActivate: [AuthGuard]
  }, 
  {
    path:'view_supplier',
    loadComponent: () => import('./it-admin/suppliers/view-supplier/view-supplier.component').then(c => c.ViewSupplierComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'asset_categories',
    loadComponent: () => import('./it-admin/asset-categories/asset-categories.component').then(c => c.AssetCategoriesComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'add_category',
    loadComponent: () => import('./it-admin/asset-categories/add-asset-category/add-asset-category.component').then(c => c.AddAssetCategoryComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'edit_category/:id',
    loadComponent: () => import('./it-admin/asset-categories/add-asset-category/add-asset-category.component').then(c => c.AddAssetCategoryComponent),
    canActivate: [AuthGuard]
  }, 
  {
    path:'view_category',
    loadComponent: () => import('./it-admin/asset-categories/view-asset-category/view-asset-category.component').then(c => c.ViewAssetCategoryComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'asset_models',
    loadComponent: () => import('./it-admin/asset-models/asset-models.component').then(c => c.AssetModelsComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'add_model',
    loadComponent: () => import('./it-admin/asset-models/add-asset-model/add-asset-model.component').then(c => c.AddAssetModelComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'edit_model/:id',
    loadComponent: () => import('./it-admin/asset-models/add-asset-model/add-asset-model.component').then(c => c.AddAssetModelComponent),
    canActivate: [AuthGuard]
  }, 
  {
    path:'view_model',
    loadComponent: () => import('./it-admin/asset-models/view-asset-model/view-asset-model.component').then(c => c.ViewAssetModelComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'status',
    loadComponent: () => import('./it-admin/status/status.component').then(c => c.StatusComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'add_status',
    loadComponent: () => import('./it-admin/status/add-status/add-status.component').then(c => c.AddStatusComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'edit_status/:id',
    loadComponent: () => import('./it-admin/status/add-status/add-status.component').then(c => c.AddStatusComponent),
    canActivate: [AuthGuard]
  }, 
  {
    path:'view_status',
    loadComponent: () => import('./it-admin/status/view-status/view-status.component').then(c => c.ViewStatusComponent),
    canActivate: [AuthGuard]
  }, 
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class MasterDataRoutingModule { }
