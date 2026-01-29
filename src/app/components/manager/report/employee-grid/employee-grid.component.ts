import { CommonModule } from '@angular/common';
import { Component, Input, OnChanges, OnInit, ViewChild } from '@angular/core';
import { FormBuilder, FormControl, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { MessageService } from 'primeng/api';
import { ButtonModule } from 'primeng/button';
import { Chart } from 'chart.js';
import { ChartModule } from 'primeng/chart';
import ChartDataLabels from 'chartjs-plugin-datalabels';
import { DropdownModule } from 'primeng/dropdown';
import { IconFieldModule } from 'primeng/iconfield';
import { InputTextModule } from 'primeng/inputtext';
import { MultiSelectModule } from 'primeng/multiselect';
import { Table, TableModule } from 'primeng/table';
import { ToastModule } from 'primeng/toast';
import { ActivatedRouterService } from 'src/app/services/activated-router-service';
import * as XLSX from 'xlsx';

//Initialize to display datalabels on bars
Chart.register(ChartDataLabels);

@Component({
  selector: 'app-employee-grid',
  imports: [ReactiveFormsModule, ToastModule, CommonModule, DropdownModule, ButtonModule,
    InputTextModule, TableModule, FormsModule, IconFieldModule,MultiSelectModule, ChartModule],
    standalone:true,
  templateUrl: './employee-grid.component.html',
  styleUrls: ['./employee-grid.component.scss'],
  providers:[MessageService]
})
export class EmployeeGridComponent implements OnInit {
   @ViewChild('detailedTable') detailedTable : Table | undefined
   @ViewChild('availabilityTable') availabilityTable : Table | undefined
   @ViewChild('cumulativeTable') cumulativeTable : Table | undefined
   @ViewChild('projectDurationTable') projectDurationTable : Table | undefined
  @Input() employeeSummaryReport:any[]=[];
  @Input() employeeDetailReport:any[]=[];
  @Input() employeeCumulativeReport:any[]=[];
  @Input() employeeCumulativeChartReport:any;
  @Input() employeeAvailabilityReport:any[]=[];
  @Input() employeeProjectDurationReport:any[]=[];
  @Input() barChartData:any;
  @Input() barChartOptions:any;

  constructor(){}

  ngOnInit(): void {}

  formatIndianNumber(x: number): string {
    const [integerPart, decimalPart] = x.toString().split('.');
    const lastThree = integerPart.substring(integerPart.length - 3);
    const otherNumbers = integerPart.substring(0, integerPart.length - 3);
    const formattedInteger = otherNumbers !== ''
      ? otherNumbers.replace(/\B(?=(\d{2})+(?!\d))/g, ",") + ',' + lastThree
      : lastThree;
    return decimalPart ? `${formattedInteger}.${decimalPart}` : formattedInteger;
  }
  
  applyFilterGlobal($event:any, stringVal:any, reportType:string) {
     if(reportType == 'detailedReport') {
      this.detailedTable!.filterGlobal(($event.target as HTMLInputElement).value, stringVal);
    } else if(reportType == 'availabilityReport') {
      this.availabilityTable!.filterGlobal(($event.target as HTMLInputElement).value, stringVal);
    } else if(reportType == 'cumulativeReport') {
      this.cumulativeTable!.filterGlobal(($event.target as HTMLInputElement).value, stringVal);
    } else if(reportType == 'employeeProjectDurationReport') {
      this.projectDurationTable!.filterGlobal(($event.target as HTMLInputElement).value, stringVal);
    }
  }

   exportToExcel(): void {
    if(this.employeeSummaryReport.length>0){
      // const worksheet: XLSX.WorkSheet = XLSX.utils.json_to_sheet(this.employeeSummaryReport);
      // const workbook: XLSX.WorkBook = { 
      //   Sheets: { 'data': worksheet },
      //   SheetNames: ['data']
      // };
      // const excelBuffer: any = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
      // this.saveExcelFile(excelBuffer, 'Employee_Summary_Report.xlsx');
      const worksheetData = [
        ['Employee Name', 'Employee Country', 'Project Country', 'Project Code', 'Project Name', 
          'Project Type', 'Allocation %', 'Start Date', 'End Date', 'Total Allocated Hours(A)',
        'Allocated Hours(till date)(B)', 'Total Worked Hours(C)', 'Utilization[(C/B) * 100]'],
        ...this.employeeSummaryReport.map((item) => [          
          item.employee_name,
          item.country,
          item.project_country,
          item.project_code,
          item.description,
          item.project_type,
          item.allocation_percent,
          // item.delivery_model,
          item.start_date,
          item.end_date,
          item.total_allocated_hours,
          item.till_allocated_hours,
          item.total_worked_hours,
          item.till_utilization
        ]),
      ];
    
      const worksheet: XLSX.WorkSheet = XLSX.utils.aoa_to_sheet(worksheetData);
      const workbook: XLSX.WorkBook = {
        Sheets: { 'data': worksheet },
        SheetNames: ['data']
      };
    
      const excelBuffer: any = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });  
      const filename = 'Employee Summary Report.xlsx';
      this.saveExcelFile(excelBuffer, filename);
    }
    
    if(this.employeeDetailReport.length>0){
      const worksheetData = [
        ['Employee Name', 'Employee Country', 'Project Country', 'Project Code', 'Project Name', 
          'Project Type', 'Delivery Model', 'Start Date', 'End Date', 'Phase', 'Total Allocated Hours(A)',
        'Allocated Hours(till date)(B)', 'Total Worked Hours(C)', 'Utilization[(C/B) * 100]'],
        ...this.employeeDetailReport.map((item) => [          
          item.employee_name,
          item.country,
          item.project_country,
          item.project_code,
          item.description,
          item.project_type,
          item.delivery_model,
          item.start_date,
          item.end_date,
          item.task,
          item.total_allocated_hours,
          item.till_allocated_hours,
          item.total_worked_hours,
          item.till_utilization
        ]),
      ];
    
      const worksheet: XLSX.WorkSheet = XLSX.utils.aoa_to_sheet(worksheetData);
      const workbook: XLSX.WorkBook = {
        Sheets: { 'data': worksheet },
        SheetNames: ['data']
      };
    
      const excelBuffer: any = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });  
      const filename = 'Employee Detailed Report.xlsx';
      this.saveExcelFile(excelBuffer, filename);
    }
    
    if(this.employeeProjectDurationReport.length>0){
      const worksheetData = [
        ['Project Name','Employee Id', 'Employee Name', 'Project Specific Hire' ,'Contractor', 'Primary Skill(s)', 'Secondary Skill(s)', 'Employee End Date' ,'Allocation %(as on end date)'],
        ...this.employeeProjectDurationReport.map((item:any) => [          
          item.project_name,
          item.employee_no,
          item.employee_name,
          item.project_specific,
          item.contractor,
          item.skillset_primary,
          item.skillset_secondary,
          item.employee_end_date,
          item.allocation_percent
        ]),
      ];
    
      const worksheet: XLSX.WorkSheet = XLSX.utils.aoa_to_sheet(worksheetData);
      const workbook: XLSX.WorkBook = {
        Sheets: { 'data': worksheet },
        SheetNames: ['data']
      };
    
      const excelBuffer: any = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });  
      const filename = 'Employee Project Duration Report.xlsx';
      this.saveExcelFile(excelBuffer, filename);
    }

    if(this.employeeCumulativeReport.length>0){
      const worksheetData = [
        ['Employee Id', 'Employee Name', 'Billable Hours' ,'Non Billable Hours', 'Utilization %'],
        ...this.employeeCumulativeReport.map((item:any) => [          
          item.employee_code,
          item.employee_name,
          item.billable_hours,
          item.non_billable_hours,
          item.utilization_percentage
        ]),
      ];
    
      const worksheet: XLSX.WorkSheet = XLSX.utils.aoa_to_sheet(worksheetData);
      const workbook: XLSX.WorkBook = {
        Sheets: { 'data': worksheet },
        SheetNames: ['data']
      };
    
      const excelBuffer: any = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });  
      const filename = 'Employee Utilization Cumulative Report.xlsx';
      this.saveExcelFile(excelBuffer, filename);
    }
    
    if(this.employeeAvailabilityReport.length>0){
      const worksheetData = [
        ['Employee Id', 'Employee Name', 'Primary Skill(s)', 'Secondary Skill(s)', 'Allocation %', 'Availability Date'],
        ...this.employeeAvailabilityReport.map((item) => [          
          item.employee_code,
          item.employee_name,
          item.primary_skill,
          item.secondary_skill,
          // item.project_name,
          item.allocation_percent,
          item.availability_date
        ]),
      ];
    
      const worksheet: XLSX.WorkSheet = XLSX.utils.aoa_to_sheet(worksheetData);
      const workbook: XLSX.WorkBook = {
        Sheets: { 'data': worksheet },
        SheetNames: ['data']
      };
    
      const excelBuffer: any = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });  
      const filename = 'Employee Availability Report.xlsx';
      this.saveExcelFile(excelBuffer, filename);
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
