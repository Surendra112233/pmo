import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { DropdownModule } from 'primeng/dropdown';
import { CalendarModule } from 'primeng/calendar';
import { DisableKeysDirective } from 'src/app/directives/disable-keys.directive';
import { ToastModule } from 'primeng/toast';
import { DialogModule } from 'primeng/dialog';
import { MessageService } from 'primeng/api';
import * as XLSX from 'xlsx';
import { PMOService } from 'src/app/services/pmo.service';
import { ActivatedRouterService } from 'src/app/services/activated-router-service';
// import * as FileSaver from 'file-saver';

@Component({
  standalone: true,
  selector: 'app-pmo-report-summary',
  templateUrl: './pmo-report-summary.component.html',
  styleUrls: ['./pmo-report-summary.component.scss'],
  imports: [CommonModule, FormsModule, DropdownModule, CalendarModule, 
    DisableKeysDirective, ToastModule, DialogModule]
})

export class PmoReportSummaryComponent implements OnInit {
  fromDate!: string;
  toDate!: string;
  workLogs: any = [];
  dateHeaders: string[] = [];
  selectedProject: any;
  projects:any = [];

  constructor(private http: HttpClient,
              private messageService: MessageService,
              private pmoService: PMOService,
              private activatedRouterService: ActivatedRouterService
  ) {}

  ngOnInit(): void {
    this.getProjects();  
  }

  getProjects(){
    this.pmoService.getProjects().subscribe(res=>{
     this.projects=res['data'];
     this.projects = this.projects.map((project:any) => ({
      ...project,
      formattedLabel: `${project.project_description} - ${project.project_code}`  // Concatenating code & name
    }));
    this.projects.sort((a:any, b:any) => a.project_description.localeCompare(b.project_description));
   },(err: any) => { 
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

  fetchWorkLogs() {

    if (!this.fromDate || !this.toDate || !this.selectedProject) {
      return;
    }
  
    const from = this.formatLocalDate(this.fromDate);
    const to = this.formatLocalDate(this.toDate);
    const payload = {
      "start_date": from,
      "end_date": to,
      "project_code": this.selectedProject
    }
  
    this.pmoService.getPMOReport(payload).subscribe((res) => {
      this.workLogs = res;
      this.dateHeaders = this.generateDateRange(from, to);
    });
    
    this.dateHeaders = this.generateDateRange(this.fromDate, this.toDate)

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
      this.selectedProject &&
      new Date(this.toDate) >= new Date(this.fromDate)
    );
  }

  isDateValid() {
    return this.fromDate && this.toDate && new Date(this.toDate) < new Date(this.fromDate)
  }

  // dialog related logic starts here
  showBreakupDialog = false;
  selectedBreakupData: any[] = [];
  selectedEmployee: string = '';
  selectedDate: string = '';
  totalWorkedHours: string = '';

  openBreakupDialog(log: any, date: string): void {
    this.selectedEmployee = log.employee_name;
    this.selectedDate = date;
    this.totalWorkedHours = log?.log[date]?.total_hours;

    const cellData = log.log[date];
    this.selectedBreakupData = Array.isArray(cellData?.details) ? cellData.details : [];
    this.showBreakupDialog = true;
  }

  openTotalBreakupDialog(log: any) {
    this.selectedEmployee = log.employee_name;
    this.totalWorkedHours = log.total;

    const employee = this.workLogs.find((worklog:any) => worklog.employee_code === log.employee_code);
    this.selectedBreakupData = [];
    // console.log(Object.entries(employee.log))
  
    if (employee && employee.log) {
      for (const [date, logEntry] of Object.entries(employee.log)) {
        const entry = logEntry as {
          details: {
            date: string,
            emp_code: string,
            emp_name: string,
            project_name: string,
            phase: string;
            task_description: string;
            worked_hours: string;
            remarks: string;
            status: string;
          }[];
        };
  
        entry.details.forEach((detail: any) => {
          this.selectedBreakupData.push({
            ...detail,
            // date, // optional, if you want to include it
          });
        });
      }
      
      // Sort selectedBreakupData by date in ascending order
      this.selectedBreakupData.sort((a, b) =>
        new Date(a.date).getTime() - new Date(b.date).getTime()
      );
      this.showBreakupDialog = true;
    }
  }

  formatDateToDDMMYYYY(dateString: string): string {
    const date = new Date(dateString);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}-${month}-${year}`;
  }

  isDownloadVisible(): boolean {
    if (!this.totalWorkedHours) return false;
  
    const [hours, minutes] = this.totalWorkedHours.split(':').map(Number);
    return (hours + minutes) > 0;
  }  

  downloadXLSX(): void {
    const worksheetData = [
      ['Date', 'Employee Code', 'Employee Name', 'Project Name' ,'Phase', 'Task Description', 'Worked HRS', 'Remarks', 'Status'],
      ...this.selectedBreakupData.map((item) => [
        // this.selectedDate,
        // this.selectedEmployee,
        item.date = this.formatDateToDDMMYYYY(item.date),
        item.emp_code,
        item.emp_name,
        item.project_name,
        item.phase,
        item.task_description,
        item.worked_hours,
        item.remarks,
        item.status,
      ]),
    ];
  
    const worksheet: XLSX.WorkSheet = XLSX.utils.aoa_to_sheet(worksheetData);
    const workbook: XLSX.WorkBook = {
      Sheets: { 'Work Log': worksheet },
      SheetNames: ['Work Log']
    };
  
    const excelBuffer: any = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });  
    const filename = `${this.selectedEmployee}_${this.selectedDate}.xlsx`;
    this.saveExcelFile(excelBuffer, filename);
  }

  // Function to save the Excel file
  private saveExcelFile(buffer: any, filename: string): void {
    const data: Blob = new Blob([buffer], { type: 'application/octet-stream' }); // Removed bookType
    const link = document.createElement('a');
    link.href = URL.createObjectURL(data);
    link.download = filename;
    link.click();
  }

}
