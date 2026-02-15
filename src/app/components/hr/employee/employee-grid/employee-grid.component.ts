import { CommonModule } from '@angular/common';
import { Component, OnInit, ViewChild } from '@angular/core';
import { Table, TableModule } from 'primeng/table';
import { IconFieldModule } from 'primeng/iconfield';
import { InputIconModule } from 'primeng/inputicon';
import { Router } from '@angular/router';
import { ConfirmationService, MessageService } from 'primeng/api'
import { ToastModule } from 'primeng/toast';
import { DialogModule } from 'primeng/dialog';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { CheckboxModule } from 'primeng/checkbox';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MasterDataService } from '../../../../services/master-data.service';
import { ActivatedRouterService } from '../../../../services/activated-router-service';
import {Employee} from '../../../../models/employee';

@Component({
    selector: 'app-employee-grid',
    imports: [TableModule, CommonModule, InputIconModule, IconFieldModule, ToastModule, DialogModule,
        ConfirmDialogModule, CheckboxModule, FormsModule, ReactiveFormsModule],
    templateUrl: './employee-grid.component.html',
    styleUrls: ['./employee-grid.component.scss'],
    providers: [ConfirmationService, MessageService],
    standalone:true
})
export class EmployeeGridComponent implements OnInit{
  @ViewChild('dt2') dt : Table | undefined
  employeeDetails:Employee[]=[];
constructor(private router:Router,private masterDataService:MasterDataService,
  private activatedRouterService:ActivatedRouterService,private messageService:MessageService){}

  status = [
    {id:'all', name: 'All'},
    {id:'active', name: 'Active'},
    {id:'inactive', name: 'Inactive'}
  ];
  selectedStatus = 'active';
  filteredData:any = [];

  ngOnInit(): void {
    this.getEmployeeDetailsByStatus();
  }

  applyFilterGlobal($event:any, stringVal:any) {
    this.dt!.filterGlobal(($event.target as HTMLInputElement).value, stringVal);
  }

  onStatusChange() {
    this.getEmployeeDetailsByStatus();
  }

  getEmployeeDetailsByStatus(){
    if(this.selectedStatus === 'all') {
      this.masterDataService.getEmployeeDetails().subscribe(res=>{
        this.handleEmployeeResponse(res); 
      },(err: any) => { 
        this.activatedRouterService.updateError(err, this.messageService)
      })

    } else {
      const isActiveFlag = this.selectedStatus === 'active';
      this.masterDataService.getActiveEmployeeDetails(isActiveFlag).subscribe(res=>{
        this.handleEmployeeResponse(res);      
      },(err: any) => { 
        this.activatedRouterService.updateError(err, this.messageService)
      })
    }
  }

  private handleEmployeeResponse(res:any) {
    this.employeeDetails = res['data'];
    this.employeeDetails = this.employeeDetails.sort((a:any, b:any) => {
      const dateA = new Date(a.updated_at || a.created_at).getTime();
      const dateB = new Date(b.updated_at || b.created_at).getTime();
      return dateB - dateA; // Descending order
    });

    this.filteredData = [...this.employeeDetails];
  }

  navigateToGrid(){
    this.router.navigate(['/hr/employees']);
  }

  addEmployee(){
    this.router.navigate(['/hr/add_employee']);
  }

  navigateToView(employee_code:number){
    this.router.navigate(['/hr/view_employee'], { queryParams: { id: employee_code} });
  }
 
}
