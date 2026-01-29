import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AuthGuard } from 'src/app/services/auth.guard';

const routes: Routes = [
  {
    path:'project-assignment',
    loadComponent: () => import('./project-assignment-grid/project-assignment-grid.component').then(c => c.ProjectAssignmentGridComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'add-project-assignment',
    loadComponent: () => import('./add-project-assignment/add-project-assignment.component').then(c => c.AddProjectAssignmentComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'view-project-assignment',
    loadComponent: () => import('./view-project-assignment/view-project-assignment.component').then(c => c.ViewProjectAssignmentComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'edit-project-assignment/:id',
    loadComponent: () => import('./add-project-assignment/add-project-assignment.component').then(c => c.AddProjectAssignmentComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'summary-report',
    loadComponent: () => import('./pmo-report-summary/pmo-report-summary.component').then(c => c.PmoReportSummaryComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'allocation_percent',
    loadComponent: () => import('./add-allocation-percent/add-allocation-percent.component').then(c => c.AddAllocationPercentComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'view_allocation_percent',
    loadComponent: () => import('./view-allocation-percent/view-allocation-percent.component').then(c => c.ViewAllocationPercentComponent),
    canActivate: [AuthGuard]
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class PMORoutingModule { }
