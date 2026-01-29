import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AuthGuard } from 'src/app/services/auth.guard';

const routes: Routes = [
  {
        path:'mnt-approval',
        loadComponent: () => import('../manager/timesheet-approval/timesheet-approval.component').then(c => c.TimesheetApprovalComponent),
        canActivate: [AuthGuard]
      },
      {
        path:'mnt-utilization',
        loadComponent: () => import('../manager/report/report.component').then(c => c.ReportComponent),
        canActivate: [AuthGuard]
      },
      {
        path:'mnt-timeLog',
        loadComponent: () => import('../hr/hr-reports/hr-reports.component').then(c => c.HrReportsComponent),
        canActivate: [AuthGuard]
      },
      {
        path:'mnt-dashboard',
        loadComponent: () => import('../manager/manager-dashboard/manager-dashboard.component').then(c => c.ManagerDashboardComponent),
        canActivate: [AuthGuard]
      }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class ManagemnetRoutingModule { }
