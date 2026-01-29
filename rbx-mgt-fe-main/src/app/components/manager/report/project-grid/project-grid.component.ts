import { CommonModule } from '@angular/common';
import { AfterViewInit, Component, Input, OnChanges, OnInit, SimpleChanges } from '@angular/core';
import { FormBuilder, FormControl, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { MessageService } from 'primeng/api';
import { ButtonModule } from 'primeng/button';
import { DropdownModule } from 'primeng/dropdown';
import { IconFieldModule } from 'primeng/iconfield';
import { InputTextModule } from 'primeng/inputtext';
import { MultiSelectModule } from 'primeng/multiselect';
import { TableModule } from 'primeng/table';
import { ToastModule } from 'primeng/toast';
import { ActivatedRouterService } from 'src/app/services/activated-router-service';
import * as XLSX from 'xlsx';
@Component({
  selector: 'app-project-grid',
  imports: [ReactiveFormsModule, ToastModule, CommonModule, DropdownModule, ButtonModule,
    InputTextModule, TableModule, FormsModule, IconFieldModule,MultiSelectModule],
    standalone:true,
  templateUrl: './project-grid.component.html',
  styleUrls: ['./project-grid.component.scss'],
  providers:[MessageService]
})
export class ProjectGridComponent implements OnInit, OnChanges{
  @Input() projectSummaryReport:any[]=[];
  @Input() projectDetailReport:any[]=[];
  @Input() projectSummaryPeriodReport:any[]=[];
  @Input() projectDetailPeriodReport:any[]=[];
  @Input() projectWiseEmpDetailsReport:any[]=[];

  month_year:string = '';
  constructor(){}
  
  ngOnInit(): void {}

  ngOnChanges(changes: SimpleChanges) {
    if (changes['projectSummaryPeriodReport'] && this.projectSummaryPeriodReport.length > 0) {
      this.projectSummaryPeriodReport.forEach((project: any) => {
        this.month_year = project.month_year;
      });
    }

    if (changes['projectDetailPeriodReport'] && this.projectDetailPeriodReport.length > 0) {
      this.projectDetailPeriodReport.forEach((project: any) => {
        this.month_year = project.month_year;
      });
    }
  }

  formatIndianNumber(x: number): string {
    const [integerPart, decimalPart] = x.toString().split('.');
    const lastThree = integerPart.substring(integerPart.length - 3);
    const otherNumbers = integerPart.substring(0, integerPart.length - 3);
    const formattedInteger = otherNumbers !== ''
      ? otherNumbers.replace(/\B(?=(\d{2})+(?!\d))/g, ",") + ',' + lastThree
      : lastThree;
    return decimalPart ? `${formattedInteger}.${decimalPart}` : formattedInteger;
  } 

  exportToExcel(): void {
    if(this.projectSummaryReport.length>0){
      const worksheet: XLSX.WorkSheet = XLSX.utils.json_to_sheet(this.projectSummaryReport);
      const workbook: XLSX.WorkBook = { 
        Sheets: { 'data': worksheet },
        SheetNames: ['data']
      };
      const excelBuffer: any = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
      this.saveExcelFile(excelBuffer, 'Project Summary Report.xlsx');
    }

    if(this.projectDetailReport.length>0){
      const worksheet: XLSX.WorkSheet = XLSX.utils.json_to_sheet(this.projectDetailReport);
      const workbook: XLSX.WorkBook = { 
        Sheets: { 'data': worksheet },
        SheetNames: ['data']
      };
      const excelBuffer: any = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
      this.saveExcelFile(excelBuffer, 'Project Detail Report.xlsx');
    }

    if(this.projectSummaryPeriodReport.length>0){
      // Get table element
      const table = document.getElementById('summary-period-report-table');
      if (!table) return;

      // Convert the table to a worksheet (preserves both headers)
      const ws: XLSX.WorkSheet = XLSX.utils.table_to_sheet(table, { raw: true });

      // Create a workbook and add the worksheet
      const wb: XLSX.WorkBook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, 'Projects');

      // Generate Excel file and trigger download
      const wbout = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
      this.saveExcelFile(wbout, 'Project Summary - Period Wise Report.xlsx');
    }

    if(this.projectDetailPeriodReport.length>0){
      // Get table element
      const table = document.getElementById('detail-period-report-table');
      if (!table) return;

      // Convert the table to a worksheet (preserves both headers)
      const ws: XLSX.WorkSheet = XLSX.utils.table_to_sheet(table, { raw: true });

      // Create a workbook and add the worksheet
      const wb: XLSX.WorkBook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, 'Projects');

      // Generate Excel file and trigger download
      const wbout = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
      this.saveExcelFile(wbout, 'Project Detail - Period Wise Report.xlsx');
    }

    if(this.projectWiseEmpDetailsReport.length>0){
      const worksheetData = [
        ['Employee Id', 'Employee Name', 'Start Date(min of Phases)', 'End Date(max of Phases)', 'Allocated Hours', 'Worked Hours', 'Pending for Approval'],
        ...this.projectWiseEmpDetailsReport.map((item) => [          
          item.employee_code,
          item.employee_name,
          item.start_date,
          item.end_date,
          item.allocated_hours,
          item.worked_hours,
          item.pending_hours
        ]),
      ];

      const worksheet: XLSX.WorkSheet = XLSX.utils.json_to_sheet(worksheetData);
      const workbook: XLSX.WorkBook = { 
        Sheets: { 'data': worksheet },
        SheetNames: ['data']
      };
      const excelBuffer: any = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
      this.saveExcelFile(excelBuffer, 'Project Wise Employee Details Report.xlsx');
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
