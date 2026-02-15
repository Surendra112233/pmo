import { CommonModule } from '@angular/common';
import { AfterViewInit, Component, Input, OnChanges, OnInit, SimpleChanges, ViewChild } from '@angular/core';
import { FormBuilder, FormControl, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { MessageService } from 'primeng/api';
import { ButtonModule } from 'primeng/button';
import { DropdownModule } from 'primeng/dropdown';
import { IconFieldModule } from 'primeng/iconfield';
import { InputTextModule } from 'primeng/inputtext';
import { MultiSelectModule } from 'primeng/multiselect';
import { Table, TableModule } from 'primeng/table';
import { ToastModule } from 'primeng/toast';
import { ActivatedRouterService } from 'src/app/services/activated-router-service';
import * as XLSX from 'xlsx';

@Component({
  standalone: true,
  selector: 'app-hr-emp-report',
  templateUrl: './hr-emp-report.component.html',
  styleUrls: ['./hr-emp-report.component.scss'],
  imports: [ReactiveFormsModule, ToastModule, CommonModule, DropdownModule, ButtonModule,
      InputTextModule, TableModule, FormsModule, IconFieldModule,MultiSelectModule],
  providers:[MessageService]
})
export class HrEmpReportComponent {

  @Input() employeeSummaryReport:any[]=[];
  @Input() employeeDetailReport:any[]=[];
  @Input() employeeSummaryProjectWiseReport:any[]=[];
  @Input() missedEntriesReport:any[]=[];
  @Input() selectedReportType:string='';
  @ViewChild('dt2') dt : Table | undefined
  constructor(private messageService:MessageService,
              private activatedRouterService:ActivatedRouterService
  ){}

  applyFilterGlobal($event:any, stringVal:any) {
    this.dt!.filterGlobal(($event.target as HTMLInputElement).value, stringVal);
  }

   exportToExcel(): void {
      if(this.employeeSummaryReport.length>0){
      const worksheet: XLSX.WorkSheet = XLSX.utils.json_to_sheet(this.employeeSummaryReport);
      const workbook: XLSX.WorkBook = { 
        Sheets: { 'data': worksheet },
        SheetNames: ['data']
      };
      const excelBuffer: any = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
      this.saveExcelFile(excelBuffer, 'Employee Summary Report.xlsx');
    }
    
    if(this.employeeDetailReport.length>0){
      const worksheet: XLSX.WorkSheet = XLSX.utils.json_to_sheet(this.employeeDetailReport);
      const workbook: XLSX.WorkBook = { 
        Sheets: { 'data': worksheet },
        SheetNames: ['data']
      };
      const excelBuffer: any = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
      this.saveExcelFile(excelBuffer, 'Employee Detail Report.xlsx');
    }

    if(this.missedEntriesReport.length>0){
      const worksheet: XLSX.WorkSheet = XLSX.utils.json_to_sheet(this.missedEntriesReport);
      const workbook: XLSX.WorkBook = { 
        Sheets: { 'data': worksheet },
        SheetNames: ['data']
      };
      const excelBuffer: any = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
      this.saveExcelFile(excelBuffer, 'Missed Timesheet Entries Report.xlsx');
    }
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
