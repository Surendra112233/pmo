import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AuthGuard } from 'src/app/services/auth.guard';

const routes: Routes = [
  {
      path:'dh-approval',
      loadComponent: () => import('../manager/timesheet-approval/timesheet-approval.component').then(c => c.TimesheetApprovalComponent),
      canActivate: [AuthGuard]
    },
    {
      path:'dh-utilization',
      loadComponent: () => import('../manager/report/report.component').then(c => c.ReportComponent),
      canActivate: [AuthGuard]
    },
    {
      path:'dh-timeLog',
      loadComponent: () => import('../hr/hr-reports/hr-reports.component').then(c => c.HrReportsComponent),
      canActivate: [AuthGuard]
    },
    {
      path:'dh-dashboard',
      loadComponent: () => import('../manager/manager-dashboard/manager-dashboard.component').then(c => c.ManagerDashboardComponent),
      canActivate: [AuthGuard]
    }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class DeliveryHeadRoutingModule { }
