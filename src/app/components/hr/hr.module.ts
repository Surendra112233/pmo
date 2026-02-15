import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { HrRoutingModule } from './hr-routing.module';
import { HrEmpReportComponent } from './hr-reports/hr-emp-report/hr-emp-report.component';
import { EmployeeDashboardComponent } from '../employee-timesheet/employee-dashboard/employee-dashboard.component';


@NgModule({
  declarations: [],
  imports: [
    CommonModule,
    HrRoutingModule
  ]
})
export class HrModule { }
