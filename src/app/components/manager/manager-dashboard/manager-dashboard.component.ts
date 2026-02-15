import { Component, Input, OnInit, ViewChild } from '@angular/core';
import { Chart } from 'chart.js';
import { ChartModule } from 'primeng/chart';
import ChartDataLabels from 'chartjs-plugin-datalabels';
import { ChartOptions, ChartType } from 'chart.js';
import { ToastModule } from 'primeng/toast';
import { ActivatedRouterService } from 'src/app/services/activated-router-service';
import { MessageService } from 'primeng/api';
import { DropdownModule } from 'primeng/dropdown';
import { FormBuilder, FormControl, FormGroup, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { Table, TableModule } from 'primeng/table';
import { CommonModule } from '@angular/common';
import { MasterDataService } from 'src/app/services/master-data.service';
import { Router } from '@angular/router';
import { ManagerMeterGaugeComponent } from './manager-meter-gauge/manager-meter-gauge.component';
import { PMOService } from 'src/app/services/pmo.service';
import * as XLSX from 'xlsx';


//Initialize to display datalabels on bars
Chart.register(ChartDataLabels);

@Component({
  selector: 'app-manager-dashboard',
  templateUrl: './manager-dashboard.component.html',
  styleUrls: ['./manager-dashboard.component.scss'],
  imports: [ChartModule, ToastModule, DropdownModule, ReactiveFormsModule,
      TableModule, CommonModule, ManagerMeterGaugeComponent, FormsModule],
  standalone: true
})
export class ManagerDashboardComponent {
@ViewChild('dt1') dt1 : Table | undefined;
@ViewChild('dt2') dt2 : Table | undefined;

  roles:any = [];
  userType:string = '';
  currentEmpName:string = '';

  projects:any = [];
  selectedProject:any = '';
  
  barChartData: any;
  barChartOptions: any;
  apiResponse:any = [];
  dashboardForm!: FormGroup;
  employeeId:string='';
  tableData:any = [];
  timeLogTableData:any = [];
  empUtlTableData:any = [];

  meterPercent:number = 0;

  animatedBudgetedHours = 0;
  animatedWorkedHours = '00:00';
  animatedUtilization = 0;

  status = [
    {id:'all', name: 'All'},
    // {id:'open', name: 'Open'},
    {id:'active', name: 'Active'},
    // {id:'inactive', name: 'Inactive'},
    {id:'completed', name: 'Completed'},
  ];
  selectedStatus:string = 'active';
  filteredData:any = [];


  constructor(
    private masterDataService: MasterDataService,
    private activatedRouterService: ActivatedRouterService,
    private messageService: MessageService,
    private fb: FormBuilder,
    private router: Router,
    private pmoService:PMOService,
  ){}
 
  ngOnInit() {
    this.employeeId = localStorage.getItem('userId') || '';
    this.currentEmpName = localStorage.getItem('user_name') || '';
    this.roles = localStorage.getItem('Roles') || '';
    this.roles = this.roles.split(',');
    this.determineUserType();
    
    // if ( this.roles.includes('UserAdmin') && this.roles.includes('DataAdmin') && 
    //       this.roles.includes('HR') && this.roles.includes('ITAdmin') && 
    //       this.roles.includes('PMO') && this.roles.includes('Manager') &&
    //       this.roles.includes('Employee') && this.roles.includes('DeliveryHead') &&
    //       this.roles.includes('Management')) {
    //         this.userType = 'PMOAdmin';

    // } else if ( ((this.roles.includes('HR') && this.roles.includes('Employee'))) ||
    //       (this.roles.includes('HR')  && this.roles.includes('Manager')) ||
    //       (this.roles.includes('HR') && this.roles.length === 1) ) {
    //         this.userType = 'HR';

    // } else if ( (this.roles.includes('Employee') && this.roles.length === 1) || 
    //       (this.roles.includes('PMO') && this.roles.length === 1) || 
    //       ((this.roles.includes('Employee') && this.roles.includes('PMO'))) ) {
    //         this.userType = 'Employee';

    // } else if ( (this.roles.includes('Manager') && this.roles.includes('PMO')) ||
    //             (this.roles.includes('Manager') && this.roles.includes('Employee')) ||  
    //             (this.roles.includes('Manager') && this.roles.length === 1) ) {
    //               this.userType = 'Manager';

    // } else if ( (this.roles.includes('DeliveryHead') && this.roles.includes('PMO')) ||
    //             (this.roles.includes('DeliveryHead') && this.roles.includes('Employee')) ||  
    //             (this.roles.includes('DeliveryHead') && this.roles.length === 1) ) {
    //               this.userType = 'DeliveryHead';

    // } else if ( (this.roles.includes('Management') && this.roles.includes('PMO')) ||
    //             (this.roles.includes('Management') && this.roles.includes('Employee')) || 
    //             (this.roles.includes('Management') && this.roles.length === 1) ) {
    //               this.userType = 'Management';
    // }

    this.dashboardForm = this.fb.group({
      project_code: new FormControl()
    });

    this.getAllProjects();
  }

    filterProjectsByStatus() {
      if (this.selectedStatus === 'all') {
        this.filteredData = [...this.projects];
      } else {
        this.filteredData = this.projects?.filter(
          (project:any) => project.project_status.toLowerCase() === this.selectedStatus
        );
      }

      if (this.filteredData.length > 0) {
        // pick first project of this status
        const firstProject = this.filteredData[0];
        this.dashboardForm.get('project_code')?.setValue(firstProject.project_code);
        this.getDashboardData({ value: firstProject.project_code });
      } else {
        // reset everything if no project found
        this.dashboardForm.get('project_code')?.reset();
        this.barChartData = { labels: [], datasets: [] };
        this.empUtlTableData = [];
        this.timeLogTableData = [];
        this.animatedBudgetedHours = 0;
        this.animatedWorkedHours = '00:00';
        this.meterPercent = 0;
      }
    }

  determineUserType() {
    // | Combination                                                | Resulting `userType` |
    // | ---------------------------------------------------------- | -------------------- |
    // | `['Employee']`                                             | **Employee**         |
    // | `['Employee','Manager']`                                   | **Manager**          |
    // | `['Employee','DeliveryHead']`                              | **DeliveryHead**     |
    // | `['Employee','Management']`                                | **Management**       |
    // | `['Employee','Manager','DeliveryHead']`                    | **DeliveryHead**     |
    // | `['Employee','Manager','DeliveryHead','Management']`       | **Management**       |
    // | `['PMO','Employee','Manager','DeliveryHead','Management']` | **Management**       |
    // | `['PMO','Employee','Manager','DeliveryHead']`              | **DeliveryHead**     |
    // | `['PMO','Employee','Manager']`                             | **Manager**          |
    // | `['PMO','Employee']`                                       | **Employee**         |
    // | `['PMO','Employee', 'HR]`                                  | **HR**               |
    // | `['HR']`                                                   | **HR**               |
    // | `['HR','Employee']`                                        | **HR**               |

    if (!this.roles || this.roles.length === 0) {
      this.userType = '';
      return;
    }

    const roles = this.roles.map((r: string) => r.toLowerCase());

    // 1.Admin override — highest priority
    if (roles.includes('useradmin') || roles.includes('dataadmin')) {
      this.userType = 'PMOAdmin';
      console.log('userType:', this.userType);
      return;
    }

    // 2.HR override — second priority
    if (roles.includes('hr')) {
      this.userType = 'HR';
      console.log('userType:', this.userType);
      return;
    }

    // 3.logic for role combinations

    // PMO + Employee + Manager + DH + Management => Management
    if (roles.includes('pmo') && roles.includes('management')) {
      this.userType = 'Management';
    }
    // PMO + Employee + Manager + DH => DeliveryHead
    else if (roles.includes('pmo') && roles.includes('deliveryhead')) {
      this.userType = 'DeliveryHead';
    }
    // PMO + Employee + Manager => Manager
    else if (roles.includes('pmo') && roles.includes('manager')) {
      this.userType = 'Manager';
    }
    // PMO + Employee => Employee
    else if (roles.includes('pmo') && roles.includes('employee')) {
      this.userType = 'Employee';
    }
    // Employee + Manager + DH + Management => Management
    else if (roles.includes('management')) {
      this.userType = 'Management';
    }
    // Employee + Manager + DH => DeliveryHead
    else if (roles.includes('deliveryhead')) {
      this.userType = 'DeliveryHead';
    }
    // Employee + Manager => Manager
    else if (roles.includes('manager')) {
      this.userType = 'Manager';
    }
    // Only Employee
    else if (roles.includes('employee')) {
      this.userType = 'Employee';
    }
    else {
      this.userType = 'Employee'; // fallback
    }

    console.log('manager dashboard userType determined as:', this.userType, 'from roles:', this.roles);
  }
  
  // getAllProjects() {
  //   this.pmoService.getProjects().subscribe(res=>{
  //       //display projects that are assigned to the current user
  //      this.projects = res['data']
  //      .filter((project:any) => {          
  //         if(this.userType == 'PMOAdmin') {
  //           return project;
  //         } else if(this.userType == 'HR') {
  //           return project.hr === this.currentEmpName;          
  //         } else if(this.userType == 'Manager') {
  //           return project.project_manager === this.currentEmpName;          
  //         } else if(this.userType == 'DeliveryHead') {
  //           return project.delivery_head === this.currentEmpName;          
  //         } else if(this.userType == 'Management') {
  //           return project.management === this.currentEmpName;          
  //         } else {
  //           return project;
  //         }
  //       });

  //       this.projects = this.projects.map((project:any) => ({
  //         ...project,
  //         formattedLabel: `${project.project_description} - ${project.project_code}`  // Concatenating code & name
  //       }));
        
  //       this.projects.sort((a:any, b:any) => a.project_description.localeCompare(b.project_description));
  //       console.log(this.projects);
  //       this.filterProjectsByStatus();     
  //     },(err: any) => { 
  //      this.activatedRouterService.updateError(err, this.messageService)
  //    })
  // }

  matchByCodeOrName(value?: string): boolean {
  if (!value) return false;
  if (value.includes(' - ')) {
    return value.split(' - ')[0].trim() === this.employeeId;
  }
  return (
    value.trim().toLowerCase() ===
    this.currentEmpName?.trim().toLowerCase()
  );
}

  getAllProjects() {
    console.log("manager dashboard userType is - ", this.userType);

    this.pmoService.getProjects().subscribe(
      res => {
        this.projects = res['data'].filter((project: any) => {
          switch (this.userType) {
            case 'PMOAdmin':
              return true;
            case 'HR':
              return project.hr?.trim().toLowerCase() === this.currentEmpName?.trim().toLowerCase();
            case 'Manager':
              // return project.project_manager?.trim().toLowerCase() === this.currentEmpName?.trim().toLowerCase();
              return  this.matchByCodeOrName(project.project_manager);
            case 'DeliveryHead':
              // return project.delivery_head?.trim().toLowerCase() === this.currentEmpName?.trim().toLowerCase();
              return  this.matchByCodeOrName(project.delivery_head);
            case 'Management':
              return project.management?.trim().toLowerCase() === this.currentEmpName?.trim().toLowerCase();
            default:
              return false;
          }
        });

        this.projects = this.projects.map((project: any) => ({
          ...project,
          formattedLabel: `${project.project_description} - ${project.project_code}`,
        }));
        this.projects.sort((a: any, b: any) => a.project_description.localeCompare(b.project_description));
        console.log(this.projects);
        this.filterProjectsByStatus(); 
      },
      (err: any) => {
        this.activatedRouterService.updateError(err, this.messageService);
      }
    );
  }

  getDashboardData(event:any){
    this.selectedProject = event.value;
    this.getApiResponse(this.selectedProject);
  }

  getApiResponse(projectCode:string) {
    // console.log(projectCode);
    this.masterDataService.getManagerDashboardResponse(projectCode).subscribe((res:any)=>{
      this.apiResponse = res;
      this.genarateUtilizationTable();
      this.genarateMeterGauge();
      this.genarateBarChart();
      this.genarateEmpUtlTable();
      this.genarateTimeLogTable();
    }, (err:any) => {
        this.activatedRouterService.updateError(err, this.messageService);
    })
  }

  genarateUtilizationTable() {
    this.tableData = this.apiResponse.tableData;
    // this.tableData = [this.apiResponse.tableData];

    this.animateBudgetedHours();
    this.animateUtilization();
    this.animateWorkedHours();
  }

  animateBudgetedHours() {
    const target = this.tableData.total_allocated_hours;
    // const target = this.tableData.allocated_budgeted_hours;
    const step = target / 50;
    let current = 0;

    const interval = setInterval(() => {
      current += step;
      if (current >= target) {
        this.animatedBudgetedHours = target;
        clearInterval(interval);
      } else {
        this.animatedBudgetedHours = Math.floor(current);
      }
    }, 20);
  }

  animateUtilization() {
    const target =  +this.tableData.Utilization; // e.g., 0.01
    const step = target / 50;
    let current = 0;

    const interval = setInterval(() => {
      current += step;
      if (current >= target) {
        this.animatedUtilization = target;
        clearInterval(interval);
      } else {
        this.animatedUtilization = current;
      }
    }, 20);
  }

  animateWorkedHours() {
    const [targetHours, targetMinutes] = this.tableData.worked_hours.split(':').map(Number);
    const totalTargetMinutes = targetHours * 60 + targetMinutes;
    let currentMinutes = 0;
    const step = Math.ceil(totalTargetMinutes / 50);

    const interval = setInterval(() => {
      currentMinutes += step;
      if (currentMinutes >= totalTargetMinutes) {
        this.animatedWorkedHours = this.tableData.worked_hours;
        clearInterval(interval);
      } else {
        const hrs = Math.floor(currentMinutes / 60);
        const mins = currentMinutes % 60;
        this.animatedWorkedHours = `${this.padZero(hrs)}:${this.padZero(mins)}`;
      }
    }, 20);
  }

  padZero(num: number): string {
    return num < 10 ? '0' + num : num.toString();
  }

  genarateMeterGauge() {
    this.meterPercent = this.apiResponse.meterdata.percentage;    
  }

  genarateBarChart() {
    this.barChartData = {
      labels: this.apiResponse.chartData.labels,
      // labels: ['Phase 1', 'Phase 2', 'Phase 3', 'Phase 4'],
      datasets: [
        {
          label: 'Allocated Hours',
          backgroundColor: '#42A5F5',
          data: this.apiResponse.chartData.allocated_hours,
          // data: [40, 35, 50, 45], // Example values
          // barThickness: 18,
        },
        {
          label: 'Worked Hours',
          backgroundColor: '#FFA726',
          data: this.apiResponse.chartData.worked_hours,
          // data: [38, 30, 48, 40], // Example values
          // barThickness: 18,
        },
      ]
    };
 
    this.barChartOptions = {
      // indexAxis: 'y', // Horizontal bars
      responsive: true,
      // animation: false,
      animation: {
        duration: 1000, // Animation duration in ms
        easing: 'easeOutQuart', // Smooth easing
      },
      plugins: {
        legend: {
          display: true,
          position: 'bottom',
          labels: {
            usePointStyle: true,         // <- Enables custom shape
            pointStyle: 'rectRounded'    // <- Options: 'circle', 'rect', 'rectRounded', 'triangle', 'line'
          },
          onHover: function (event:any) {
            event.native.target.style.cursor = 'pointer';  // Show pointer cursor
          },
          onLeave: function (event:any) {
            event.native.target.style.cursor = 'default';  // Reset cursor
          }
        },
        tooltip: {
         // mode: 'index',
          intersect: true
        },        
        datalabels: {
          // anchor: 'end',
          // align: 'end',
          anchor: 'center',
          align: 'center',
          color: '#000',
          font: {
            weight: 'bold'
          },
          formatter: (value: number) => value === 0 ? `${value}` : `${value}`
        }
      },
       layout: {
        padding: {
          top: 25 // Adds space at the top of the chart for labels
        }
      },
      scales: {
        x: {
          stacked: false,
          title: {
            display: true,
            text: 'Phases'
          },
          ticks: {
            maxRotation: 0,
            minRotation: 0,
            autoSkip: false,  // Optional: ensures all labels are shown
            font: {
              size: 12
            }
          }
        },
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Hours'
          }
        }
      }
    };
  }

  genarateEmpUtlTable() {
    this.empUtlTableData = this.apiResponse.emp_utilization;
  }

  genarateTimeLogTable() {
    this.timeLogTableData = this.apiResponse.time_log_data;
  }

  applyFilterGlobal($event:any, stringVal:any, tableType:string) {
    if(tableType == 'empUtl') {
      this.dt1!.filterGlobal(($event.target as HTMLInputElement).value, stringVal);
    } else if(tableType == 'timeLog') {
      this.dt2!.filterGlobal(($event.target as HTMLInputElement).value, stringVal);
    }
  }

  addTimesheet() {
    this.router.navigate(['/emp/add_timesheet']);
  }

  exportToExcel(type:string): void {
    if(type== 'empUtl' && this.empUtlTableData.length>0){          
      const worksheetData = [
        ['Project Code', 'Project Name', 'Employee Code', 'Employee Name', 'Total Allocated Hours', 'Total Worked Hours', 'Utilization %'],
        ...this.empUtlTableData.map((item:any) => [
          item.project_code,
          item.project_name,
          item.employee_code,
          item.employee_name,
          item.total_allocated_hours,
          item.total_worked_hours,
          item.utilization
        ]),
      ];
      const worksheet: XLSX.WorkSheet = XLSX.utils.aoa_to_sheet(worksheetData);
      const workbook: XLSX.WorkBook = { 
        Sheets: { 'data': worksheet },
        SheetNames: ['data']
      };
      const excelBuffer: any = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
      this.saveExcelFile(excelBuffer, 'Employee_Utilization_Report.xlsx');
    }
      
    if(type== 'timeLog' && this.timeLogTableData.length>0){
      const worksheetData = [
        ['Project Code', 'Project Name', 'Employee Code', 'Employee Name', 'Missed Entries'],
        ...this.timeLogTableData.map((item:any) => [
          item.project_code,
          item.project_name,
          item.employee_code,
          item.employee_name,
          item.missed_entries
        ]),
      ];
      const worksheet: XLSX.WorkSheet = XLSX.utils.aoa_to_sheet(worksheetData);
      const workbook: XLSX.WorkBook = { 
        Sheets: { 'data': worksheet },
        SheetNames: ['data']
      };
      const excelBuffer: any = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
      this.saveExcelFile(excelBuffer, 'Time_Log_Report.xlsx');
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
