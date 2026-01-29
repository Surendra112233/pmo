import { Component, OnInit, ViewChild } from '@angular/core';
import { Router } from '@angular/router';
import { Table, TableModule } from 'primeng/table';
import { IconFieldModule } from 'primeng/iconfield';
import { InputIconModule } from 'primeng/inputicon';
import { ConfirmationService, MessageService } from 'primeng/api'
import { ToastModule } from 'primeng/toast';
import { DialogModule } from 'primeng/dialog';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { CheckboxModule } from 'primeng/checkbox';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { EmployeeService} from '../../../services/employee.service';
import { ActivatedRouterService } from '../../../services/activated-router-service';
import { MasterDataService } from 'src/app/services/master-data.service';
import { LoginService } from 'src/app/services/login.service';

@Component({
    selector: 'app-timesheet-view',
    imports: [TableModule, CommonModule, InputIconModule, IconFieldModule, ToastModule, DialogModule,
        ConfirmDialogModule, CheckboxModule, FormsModule, ReactiveFormsModule],
    templateUrl: './timesheet-view.component.html',
    styleUrls: ['./timesheet-view.component.scss'],
    providers: [MessageService],
    standalone:true
})
export class TimesheetViewComponent implements OnInit{
 @ViewChild('dt2') dt : Table | undefined
 timesheetData:any[]=[];
 imgSrc='src/assets/images/timesheet.svg';
 loggedUserId:string='';
 allPhases:any = [];
 month:any = '';
 currentMonth:any = '';
 currentYear:any = '';

  constructor(private employeeService:EmployeeService, private activatedRouterService: ActivatedRouterService,
    private router:Router, private messageService:MessageService,private masterDataService:MasterDataService,
  private loginService:LoginService) {}

  ngOnInit(): void {
    const today = new Date();
    this.currentMonth = today.getMonth() + 1;
    this.month = today.toLocaleString('default', { month: 'long' }); 
    this.currentYear = today.getFullYear();

    this.loggedUserId=localStorage.getItem("userId")||'';
    this.getTimesheetByEmployeeCode();
    // this.getAllTimesheets();
  }

  // getAllTimesheets(){
  //  this.employeeService.getTimesheets(this.loggedUserId).subscribe(res=>{
  //     const employeeTimesheetDetails =res['timesheet_entries'];
  //     this.timesheetData=employeeTimesheetDetails;
  //     // this.timesheetData=employeeTimesheetDetails.filter((task:any)=>task.employee_code==this.loggedUserId);
  //     this.masterDataService.getTasks().subscribe((res:any) => {
  //       this.allPhases = res?.['data'];
  //     })
  //   },(err: any) => {
  //     const errMsg = err?.error?.error || err;
  //     this.messageService.add({ severity: 'error', summary: '', detail: errMsg }); 
  //     // this.activatedRouterService.updateError(err, this.messageService)
  //   })
  // }

  getTimesheetByEmployeeCode() {
    const obj={
      "employee_code": this.loggedUserId,
      "month": this.currentMonth,
      "year": +this.currentYear
    };
    this.employeeService.getTimesheetByEmployeeCode(obj).subscribe(
      (res) => {
        const employeeTimesheetDetails = res['data'];
        this.timesheetData=employeeTimesheetDetails;
        this.masterDataService.getTasks().subscribe((res:any) => {
          this.allPhases = res?.['data'];
        })        
      },
      (err: any) => {
        const errMsg = err?.error?.error || err;
        this.messageService.add({ severity: 'error', summary: '', detail: errMsg });
      }
    );
  }

  formatDate(dateStr:string) {
    const date = new Date(dateStr);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0'); // Months are 0-based
    const year = String(date.getFullYear()); // Get last 2 digits
    // const year = String(date.getFullYear()).slice(-2); // Get last 2 digits
    return `${day}-${month}-${year}`;
  }

  getPhaseName(task_code: string) {
     const phase = this.allPhases.find((phase:any) => phase.task_code === task_code);
     return phase ? phase.task_group : ''
  }

  navigateToGrid() {
    this.router.navigate(['/emp/timesheet']);
  }
  addTimesheet() {
    this.router.navigate(['/emp/add_timesheet']);
  }

  navigateToView(id:string) {
    this.router.navigate(['/emp/view_timesheet'], { queryParams: { id:  id} });
  }

  applyFilterGlobal($event:any, stringVal:any) {
    this.dt!.filterGlobal(($event.target as HTMLInputElement).value, stringVal);
  }

  

}
