import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AuthGuard } from 'src/app/services/auth.guard';

const routes: Routes = [
  {
    path:'employees',
    loadComponent: () => import('./employee/employee-grid/employee-grid.component').then(c => c.EmployeeGridComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'add_employee',
    loadComponent: () => import('./employee/add-employee/add-employee.component').then(c => c.AddEmployeeComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'edit_employee/:id',
    loadComponent: () => import('./employee/add-employee/add-employee.component').then(c => c.AddEmployeeComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'view_employee',
    loadComponent: () => import('./employee/view-employee/view-employee.component').then(c => c.ViewEmployeeComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'reports',
    loadComponent: () => import('./hr-reports/hr-reports.component').then(c => c.HrReportsComponent), 
    canActivate: [AuthGuard]
  },
  {
    path:'hr_approval',
    loadComponent: () => import('./timesheet-approval/timesheet-approval.component').then(c => c.TimesheetApprovalComponent), 
    canActivate: [AuthGuard]
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class HrRoutingModule { }
