import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { DropdownModule } from 'primeng/dropdown';
import { CalendarModule } from 'primeng/calendar';
import { ToastModule } from 'primeng/toast';
import { DialogModule } from 'primeng/dialog';
import { MessageService } from 'primeng/api';
import { ActivatedRouterService } from 'src/app/services/activated-router-service';
import { MasterDataService } from 'src/app/services/master-data.service';
import { PMOService } from 'src/app/services/pmo.service';

@Component({
  standalone: true,
  selector: 'app-view-allocation-percent',
  templateUrl: './view-allocation-percent.component.html',
  styleUrls: ['./view-allocation-percent.component.scss'],
  imports: [CommonModule, FormsModule, DropdownModule, CalendarModule, 
    ToastModule, DialogModule]
})
export class ViewAllocationPercentComponent {
  fromDate!: string;
  toDate!: string;
  workLogs: any = [];
  dateHeaders: string[] = [];
  selectedEmployeeCode: any;
  employeeList:any = [];
  isEmployee: boolean = false;
  isEmpDetailsLoading: boolean = true;

  // dialog related variables
  showBreakupDialog = false;
  selectedBreakupData: any[] = [];
  selectedProjectCode: string = '';
  selectedDate: string = '';
  totalAllocation: string = '';

  constructor(private http: HttpClient,
              private messageService: MessageService,
              private masterDataService: MasterDataService,
              private pmoService: PMOService,
              private activatedRouterService: ActivatedRouterService
  ) {}

  ngOnInit(): void {
    this.selectedEmployeeCode = localStorage.getItem('userId') || '';
    
    const role = localStorage.getItem('Roles') || '';
    if (role.includes('Employee') && role.length === 1) {
      this.isEmployee = true;
    } else {
      this.isEmployee = false;
      this.getEmployees();
    }
  }

  getEmployees(){
    this.isEmpDetailsLoading = true;
    this.masterDataService.getEmployeeDetails().subscribe(res=>{
     this.employeeList=res['data'];
     this.employeeList.sort((a:any, b:any) => a.employee_code.localeCompare(b.employee_code));
      this.employeeList = this.employeeList.map((emp:any) => ({
        ...emp,
        formattedLabel: `${emp.employee_code} - ${emp.name}`  // Concatenating code & name
      }));
      this.isEmpDetailsLoading = false;
   },(err: any) => {
     this.isEmpDetailsLoading = false;
     this.activatedRouterService.updateError(err, this.messageService)
   });
  }

  onDateChange() {
    if (this.fromDate && this.toDate) {
      const diff = new Date(this.toDate).getTime() - new Date(this.fromDate).getTime();
      const maxDiff = 30 * 24 * 60 * 60 * 1000;

      if (diff > maxDiff) {
        this.messageService.add({ severity: 'error', summary: '', detail: 'Date range cannot exceed one month' });
        this.toDate = '';
      }
    }
  }

  selectEmployeeCode(event:any) {
    this.selectedEmployeeCode = event.value;
  }

  fetchWorkLogs() {

    if (!this.fromDate || !this.toDate || !this.selectedEmployeeCode) {
      return;
    }
  
    const from = this.formatLocalDate(this.fromDate);
    const to = this.formatLocalDate(this.toDate);
    const payload = {
      "start_date": from,
      "end_date": to,
      "employee_code": this.selectedEmployeeCode
    }
  
    this.pmoService.getDateRangeAllocation(payload).subscribe((res) => {
      console.log(res);

//        let res1 = [
//     {
//         "project_code": "RB001",
//         "project_name": "Internal Project",
//         "log": {
//             "2025-11-01": {
//               "details": [
//                     {
//                         "date": "2025-11-01",
//                         "project_code": "RB001",
//                         "project_name": "Internal Project",
//                         "phase": "3 Realize",
//                         "allocation_percent": 75.0,
//                     },
//                     {
//                         "date": "2025-11-01",
//                         "project_code": "RB001",
//                         "project_name": "Internal Project",
//                         "phase": "4 Deploy",
//                         "allocation_percent": 25.0,
//                         "status_flag": "multiple"
//                     }
//                 ],
//                 "allocation_percent": 100.0,
//                 "status_flag": "multiple"
//             },
//             "2025-11-02": {
//                 "details": [
//                     {
//                         "date": "2025-11-02",
//                         "project_code": "RB001",
//                         "project_name": "Internal Project",
//                         "phase": "3 Realize",
//                         "allocation_percent": 50,
//                     },
//                     {
//                         "date": "2025-11-02",
//                         "project_code": "RB001",
//                         "project_name": "Internal Project",
//                         "phase": "4 Deploy",
//                         "allocation_percent": 50,
//                     }
//                 ],
//                 "allocation_percent": 100.0,
//                 "status_flag": "multiple"
//             },
//             "2025-11-03": {
//                 "details": [
//                     {
//                         "date": "2025-11-01",
//                         "project_code": "RB001",
//                         "project_name": "Internal Project",
//                         "phase": "3 Realize",
//                         "allocation_percent": 100.0,
//                     }
//                 ],
//                 "allocation_percent": 100.0,
//                 "status_flag": "single"
//             }
//         }
//     }
// ]
      this.workLogs = res;
      this.dateHeaders = this.generateDateRange(from, to);
    });
  }

  formatLocalDate(date: any): string {
    const year = date.getFullYear();
    const month = ('0' + (date.getMonth() + 1)).slice(-2);
    const day = ('0' + date.getDate()).slice(-2);
    return `${year}-${month}-${day}`;
  }

  generateDateRange(from: string, to: string): string[] {
    const dates: string[] = [];
    let current = new Date(from);
    const end = new Date(to);
  
    while (current <= end) {
      const year = current.getFullYear();
      const month = ('0' + (current.getMonth() + 1)).slice(-2);
      const day = ('0' + current.getDate()).slice(-2);
      dates.push(`${year}-${month}-${day}`);
      current.setDate(current.getDate() + 1);
    }
  
    return dates;
  }

  isFormValid(): boolean {
    return !!(
      this.fromDate &&
      this.toDate &&
      this.selectedEmployeeCode &&
      new Date(this.toDate) >= new Date(this.fromDate)
    );
  }

  isDateValid() {
    return this.fromDate && this.toDate && new Date(this.toDate) < new Date(this.fromDate)
  }

  openBreakupDialog(log: any, date: string): void {
    this.selectedProjectCode = log.project_code;
    this.selectedDate = date;
    this.totalAllocation = log?.log[date]?.allocation_percent;

    const cellData = log.log[date];
    this.selectedBreakupData = Array.isArray(cellData?.details) ? cellData.details : [];
    this.showBreakupDialog = true;
  }
}
