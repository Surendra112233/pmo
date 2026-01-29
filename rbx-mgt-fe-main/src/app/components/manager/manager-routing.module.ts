import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AuthGuard } from 'src/app/services/auth.guard';

const routes: Routes = [
  {
    path:'approval',
    loadComponent: () => import('./timesheet-approval/timesheet-approval.component').then(c => c.TimesheetApprovalComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'utilization',
    loadComponent: () => import('./report/report.component').then(c => c.ReportComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'timeLog',
    loadComponent: () => import('../hr/hr-reports/hr-reports.component').then(c => c.HrReportsComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'mng-dashboard',
    loadComponent: () => import('./manager-dashboard/manager-dashboard.component').then(c => c.ManagerDashboardComponent),
    canActivate: [AuthGuard]
  }
];
@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class ManagerRoutingModule { }
