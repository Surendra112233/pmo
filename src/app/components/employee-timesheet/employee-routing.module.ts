import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AuthGuard } from 'src/app/services/auth.guard';


const routes: Routes = [
  {
    path:'timesheet',
    loadComponent: () => import('./timesheet-view/timesheet-view.component').then(c => c.TimesheetViewComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'add_timesheet',
    loadComponent: () => import('./add-timesheet/add-timesheet.component').then(c => c.AddTimesheetComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'view_timesheet',
    loadComponent: () => import('./timesheet-view/timesheet-view.component').then(c => c.TimesheetViewComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'timeLog',
    loadComponent: () => import('../hr/hr-reports/hr-reports.component').then(c => c.HrReportsComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'emp-dashboard',
    loadComponent: () => import('./employee-dashboard/employee-dashboard.component').then(c => c.EmployeeDashboardComponent),
    canActivate: [AuthGuard]
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class EmployeeRoutingModule { }
