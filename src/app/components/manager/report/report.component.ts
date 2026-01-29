import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
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
import { PMOService} from 'src/app/services/pmo.service';
import { MasterDataService} from 'src/app/services/master-data.service';
import { EmployeeGridComponent} from '../report/employee-grid/employee-grid.component';
import { ProjectGridComponent} from '../report/project-grid/project-grid.component';
import { ManagerService} from 'src/app/services/manager.service';
import { CalendarModule } from 'primeng/calendar';

@Component({
  selector: 'app-report',
  standalone:true,
   imports: [ReactiveFormsModule, ToastModule, CommonModule, DropdownModule, ButtonModule, CalendarModule,
          InputTextModule, TableModule, FormsModule, IconFieldModule,MultiSelectModule,ProjectGridComponent,EmployeeGridComponent],
  templateUrl: './report.component.html',
  styleUrls: ['./report.component.scss'],
  providers:[MessageService]
})
export class ReportComponent implements OnInit{
  projectReportForm!:FormGroup;
  reportType:any[]=[
    // { name:"Project Summary"},
    // { name:"Project Detailed"},
    { name:"Project Summary - Period Wise"},
    { name:"Project Detailed - Period Wise"},
    { name:"Employee Details - Project Wise"},
     {name:"Employee Summary"},
     { name:"Employee Detailed"}
  ];
  
  projectType:any[]=[
    // { name:"Project Summary"},
    // { name:"Project Detailed"},
    { name:"Project Summary - Period Wise"},
    { name:"Project Detailed - Period Wise"},
    { name:"Employee Details - Project Wise"},
    {name:"Employee Summary"},
    { name:"Employee Detailed"},
    { name:"Employee Project Duration"},
    { name:"Employee Utilization Cumulative"},
    { name:"Employee Availability"},
  ];
projects:any[]=[];
employeeDetails:any[]=[];
isProjectCode:boolean=false;
isEmployeeCode:boolean=false;
isProjectsLoading:boolean=true;
isEmloyeesLoading:boolean=true;
projectDetailReport:any[]=[];
projectSummaryReport:any[]=[];
projectSummaryPeriodReport:any[]=[];
projectDetailPeriodReport:any[]=[];
projectWiseEmpDetailsReport:any[]=[];
employeeDetailReport:any[]=[];
employeeSummaryReport:any[]=[];
employeeCumulativeReport:any[]=[];
employeeCumulativeChartReport:any;
employeeAvailabilityReport:any[]=[];
employeeProjectDurationReport:any[]=[];
roles:any;
showInputField:any;
showDurationInputField:any;
barChartData: any;
barChartOptions: any;

months = [ 
  { id: 1, name: "January" },
  { id: 2, name: "February" },
  { id: 3, name: "March" },
  { id: 4, name: "April" },
  { id: 5, name: "May" },
  { id: 6, name: "June" },
  { id: 7, name: "July" },
  { id: 8, name: "August" },
  { id: 9, name: "September" },
  { id: 10, name: "October" },
  { id: 11, name: "November" },
  { id: 12, name: "December" },
]
years: number[] = [];
selectedYear: number=new Date().getFullYear();
selectedMonth: number=new Date().getMonth() + 1;
reportPeriodType: string = '';
isPeriodWise:boolean=false;


  constructor(private formBuilder: FormBuilder,private pmoService:PMOService,private masterDataService:MasterDataService,
    private activatedRouterService: ActivatedRouterService,private messageService:MessageService,private managerService:ManagerService){}

  ngOnInit(): void {
    this.roles = localStorage.getItem('Roles');
    this.generateYearArray();
    this.buildForm();
    this.getProjects();
    this.getEmployees();
}

 buildForm(){
      this.projectReportForm = this.formBuilder.group({
        report_type: new FormControl('', [Validators.required]),
        project_code: new FormControl('', [Validators.required]),
        employee_code: new FormControl('', [Validators.required]),
        fromDate: new FormControl(''),
        toDate: new FormControl(''),
        durationDays: new FormControl('90',[Validators.min(1), Validators.max(90)]),
        availabilityDays: new FormControl('',[Validators.min(1), Validators.max(30)]),
        period_type: new FormControl(''),
        month: new FormControl(this.selectedMonth),
        year: new FormControl(this.selectedYear),
        start_date: new FormControl(''),
        end_date: new FormControl(''),
    });
  }

  getProjects(){
    this.isProjectsLoading = true;
    this.pmoService.getProjects().subscribe(res=>{
     this.projects=res['data'];
     this.projects = this.projects.map((project:any) => ({
      ...project,
      formattedLabel: `${project.project_description} - ${project.project_code}`  // Concatenating code & name
    }));
    this.projects.sort((a:any, b:any) => a.project_description.localeCompare(b.project_description));
    this.isProjectsLoading = false;
  },(err: any) => {
    this.isProjectsLoading = false;
     this.activatedRouterService.updateError(err, this.messageService)
   });
 }

 getEmployees(){
  this.isEmloyeesLoading = true
  this.masterDataService.getEmployeeDetails().subscribe(res=>{
    this.employeeDetails=res['data'].map((emp: { employee_code: any; name: any; }) => ({
      ...emp,
      employee_codewithName: `${emp.employee_code} - ${emp.name}`
    }));
    this.employeeDetails = this.employeeDetails.sort((a,b) => a.employee_code.localeCompare(b.employee_code));
    this.isEmloyeesLoading = false;
  },(err: any) => {
    this.isEmloyeesLoading = false; 
    this.activatedRouterService.updateError(err, this.messageService)
  })
 }

   generateYearArray() {
    const startYear = 2025; //as application is started on 01.04.2025
    const currentYear = new Date().getFullYear();

    // build list from current year down to startYear so latest appears on top
    this.years = [];
    for (let y = currentYear; y >= startYear; y--) {
      this.years.push(y);
    }

    // ensure selectedYear is valid and defaults to current year
    if (!this.years.includes(this.selectedYear)) {
      this.selectedYear = currentYear;
      this.projectReportForm?.get('year')?.setValue(this.selectedYear);
    }
  }

onDateChange() {
  let fromDate = this.projectReportForm.get('fromDate')?.value;
  let toDate = this.projectReportForm.get('toDate')?.value;

  if (fromDate && toDate) {
    const from = new Date(fromDate).getTime();
    const to = new Date(toDate).getTime();
    const diff = to - from;
    const maxDiff = 30 * 24 * 60 * 60 * 1000; // 30 days

    if (diff < 0) {
      this.messageService.add({ severity: 'error', summary: '', detail: 'End date must be greater than or equal to start date' });
      this.projectReportForm.get('toDate')?.setValue(null);
      return;
    }

    if (diff > maxDiff) {
      this.messageService.add({ severity: 'error', summary: '', detail: 'Date range cannot exceed one month' });
      this.projectReportForm.get('toDate')?.setValue(null);
    }
  }
}

testEnddate(end_date:any, start_date:any){
  if (start_date.value && end_date.value && start_date.value > end_date.value) {
    this.messageService.add({
        severity: 'error',
        summary: 'End Date Validation Error',
        detail: 'End date must be greater than or equal to start date.'
    });
    this.projectReportForm.controls['end_date'].setValue('');
  }
}

 onPeriodTypeChange(event: any) {
  this.reportPeriodType = event.target.value;

  // Clear existing values
  // this.projectReportForm.patchValue({
  //   month: '',
  //   year: '',
  //   start_date: '',
  //   end_date: ''
  // });

  // Clear all related validators first
  this.projectReportForm.get('month')?.clearValidators();
  this.projectReportForm.get('year')?.clearValidators();
  this.projectReportForm.get('start_date')?.clearValidators();
  this.projectReportForm.get('end_date')?.clearValidators();

  // Apply validators based on period type
  if (this.reportPeriodType === 'month_year') {
    this.projectReportForm.get('month')?.setValidators([Validators.required]);
    this.projectReportForm.get('year')?.setValidators([Validators.required]);
  } 
  else if (this.reportPeriodType === 'date_range') {
    this.projectReportForm.get('start_date')?.setValidators([Validators.required]);
    this.projectReportForm.get('end_date')?.setValidators([Validators.required]);
  }

  // Update validity after changes
  this.projectReportForm.get('month')?.updateValueAndValidity();
  this.projectReportForm.get('year')?.updateValueAndValidity();
  this.projectReportForm.get('start_date')?.updateValueAndValidity();
  this.projectReportForm.get('end_date')?.updateValueAndValidity();
}

  onChangeReportType() {
    const controls = this.projectReportForm.controls;
    const reportType = controls['report_type']?.value;

    // Reset all validators and values
    Object.keys(controls).forEach(key => {
      controls[key].clearValidators();
      controls[key].updateValueAndValidity();
    });

    controls['employee_code']?.setValue('');
    controls['project_code']?.setValue('');
    controls['period_type']?.setValue('');
    this.showInputField = false;
    this.showDurationInputField = false;
    this.reportPeriodType = '';

    switch (reportType) {
      case 'Project Summary':
      case 'Project Detailed':
      case 'Employee Details - Project Wise':
        this.isProjectCode = true;
        this.isEmployeeCode = false;
        this.isPeriodWise = false;
        controls['project_code'].setValidators([Validators.required]);
        break;

      case 'Project Summary - Period Wise':
      case 'Project Detailed - Period Wise':
        this.isPeriodWise = true;
        this.isProjectCode = true;
        this.isEmployeeCode = false;
        controls['period_type'].setValidators([Validators.required]);
        controls['project_code'].setValidators([Validators.required]);
        break;
      
      case 'Employee Project Duration':
        this.isPeriodWise = false;
        this.isProjectCode = true;
        this.showDurationInputField = true;
        this.isEmployeeCode = false;
        controls['project_code'].setValidators([Validators.required]);
        controls['durationDays'].setValidators([Validators.required]);
        break;

      case 'Employee Utilization Cumulative':
        this.isProjectCode = false;
        this.isEmployeeCode = true;
        this.isPeriodWise = false;
        controls['fromDate'].setValidators([Validators.required]);
        controls['toDate'].setValidators([Validators.required]);
        break;

      case 'Employee Availability':
        this.isProjectCode = false;
        this.isEmployeeCode = false;
        this.isPeriodWise = false;
        this.showInputField = true;
        controls['availabilityDays'].setValidators([Validators.required]);
        break;

      default:
        this.isProjectCode = false;
        this.isPeriodWise = false;
        this.isEmployeeCode = true;
        controls['employee_code'].setValidators([Validators.required]);
        break;
    }

    // Update all validators
    Object.keys(controls).forEach(key => controls[key].updateValueAndValidity());
  }

  changeDateFormat(date: any): string {
    const year = date.getFullYear();
    const month = ('0' + (date.getMonth() + 1)).slice(-2);
    const day = ('0' + date.getDate()).slice(-2);
    return `${year}-${month}-${day}`;
  }

  onSubmit() {
  // Reset all report arrays
  this.projectSummaryReport = [];
  this.projectDetailReport = [];
  this.employeeDetailReport = [];
  this.employeeSummaryReport = [];
  this.employeeCumulativeReport = [];
  this.employeeAvailabilityReport = [];
  this.projectSummaryPeriodReport = [];
  this.projectDetailPeriodReport = [];
  this.employeeProjectDurationReport = [];
  this.projectWiseEmpDetailsReport = [];

  const reportType = this.projectReportForm.controls['report_type']?.value;
  const empCode = this.projectReportForm.get('employee_code')?.value;
  const projectCode = this.projectReportForm.get('project_code')?.value;
  const availabilityDays = this.projectReportForm.get('availabilityDays')?.value;
  const durationDays = this.projectReportForm.get('durationDays')?.value;
  const month = this.projectReportForm.get('month')?.value;
  const year = this.projectReportForm.get('year')?.value;
  const start_date = this.projectReportForm.get('start_date')?.value;
  const end_date = this.projectReportForm.get('end_date')?.value;

  switch (reportType) {
    case 'Project Summary':
      if (projectCode) {
        this.getProjectSummaryReport({ project_code: projectCode });
      }
      break;

    case 'Project Detailed':
      if (projectCode) {
        this.getProjectDetailReport({ project_code: projectCode });
      }
      break;

    case 'Employee Details - Project Wise':
      if (projectCode) {
        this.getProjectWiseEmpDetailsReport({ project_code: projectCode });
      }
      break;

    case 'Project Summary - Period Wise':
      let summary_payload:any = {};
      if(this.reportPeriodType == 'month_year') {
        summary_payload = {
            "project_code": projectCode,
            "period_type": "month_year",
            "month": Number(month),
            "year": Number(year)
          }
      } else if (this.reportPeriodType == 'date_range') {
        summary_payload = {
          "project_code": projectCode,
          "period_type": "date_range",
          "from_date": this.changeDateFormat(start_date),
          "to_date": this.changeDateFormat(end_date)
        }
      }      
      this.getProjectSummaryPeriodWiseReport(summary_payload);
      break;

    case 'Project Detailed - Period Wise':
      let detailed_payload:any = {};
      if(this.reportPeriodType == 'month_year') {
        detailed_payload = {
            "project_code": projectCode,
            "period_type": "month_year",
            "month": Number(month),
            "year": Number(year)
          }
      } else if (this.reportPeriodType == 'date_range') {
        detailed_payload = {
          "project_code": projectCode,
          "period_type": "date_range",
          "from_date": this.changeDateFormat(start_date),
          "to_date": this.changeDateFormat(end_date)
        }
      }
      this.getProjectDetailedPeriodWiseReport(detailed_payload);
      break;

    case 'Employee Project Duration':
      if (durationDays) {
        this.getEmployeeProjectDurationReport(projectCode, durationDays);
      }
      break;
    
    case 'Employee Summary':
      if (empCode) {
        this.getEmployeeSummaryReport({ employee_code: empCode });
      }
      break;

    case 'Employee Detailed':
      if (empCode) {
        this.getEmployeeDetailReport({ employee_code: empCode });
      }
      break;

    case 'Employee Utilization Cumulative':
        const startDate = this.changeDateFormat(this.projectReportForm.get('fromDate')?.value);
        const endDate = this.changeDateFormat(this.projectReportForm.get('toDate')?.value);
      if (empCode) {
        this.managerService.getEmployeeCumulativeReport(empCode, startDate, endDate).subscribe(res => {
          this.employeeCumulativeReport = res.tableData || [];
          this.employeeCumulativeChartReport = res.chartData || [];

          this.genarateBarChart(); 
          if (!this.employeeCumulativeReport?.length) {
            this.messageService.add({ severity: 'error', summary: '', detail: 'No data found for the selected employee' });
          }
        }, err => this.activatedRouterService.updateError(err, this.messageService));
      } else {
        this.managerService.getAllEmployeeCumulativeReport(startDate, endDate).subscribe(res => {
          this.employeeCumulativeReport = res.tableData || [];
          this.employeeCumulativeChartReport = res.chartData || [];

          this.genarateBarChart(); 
          if (!this.employeeCumulativeReport?.length) {
            this.messageService.add({ severity: 'error', summary: '', detail: 'No data found for the selected employee' });
          }
        }, err => this.activatedRouterService.updateError(err, this.messageService));
      }
      break;

    case 'Employee Availability':
      if (availabilityDays) {
        this.managerService.getEmployeeAvailabilityReport(availabilityDays).subscribe(res => {
          this.employeeAvailabilityReport = res?.['data'] || [];
          if (!res?.['data'].length) {
            this.messageService.add({ severity: 'error', summary: '', detail: 'No data found for the selected period' });
          }
        }, err => this.activatedRouterService.updateError(err, this.messageService));
      }
      break;

    default:
      this.messageService.add({ severity: 'warn', summary: '', detail: 'Invalid report type selected' });
      break;
  }
}

genarateBarChart() {
    this.barChartData = {
      labels: this.employeeCumulativeChartReport?.labels,
      // labels: ['Expected Hours', 'Billable Hours', 'Non Billable Hours'],
      datasets: [
        {
          label: 'Value',
          backgroundColor: ['#00acc1','#42A5F5', '#FFA726', ],
          data: this.employeeCumulativeChartReport?.values,
          // data: [3200, '2750.75', 30.25], // Example values
        }
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
          display: false,
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
          intersect: true
        },        
        datalabels: {
          anchor: 'center',
          align: 'center',
          color: '#000',
          font: {
            weight: 'bold'
          },
          // formatter: (value: number) => value === 0 ? `${value}` : `${value}`
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
            display: false,
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

  getFormControl(formControlName:string) {
    return this.projectReportForm.get(formControlName);
  }

  getProjectSummaryReport(project_code:any){
    this.managerService.getProjectSummaryReport(project_code).subscribe(res=>{
      this.projectSummaryReport=res;
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    });
  }

  getProjectDetailReport(project_code:any){
    this.managerService.getProjectDetailReport(project_code).subscribe(res=>{
      this.processProjectDetailReport(res);
      //this.projectDetailReport=res;
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    });
  }
  
  getProjectSummaryPeriodWiseReport(payload:any){
    this.managerService.getProjectSummaryPeriodWiseReport(payload).subscribe(res=>{
      this.projectSummaryPeriodReport=res;
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    });
  }

  getProjectDetailedPeriodWiseReport(payload:any){
    this.managerService.getProjectDetailedPeriodWiseReport(payload).subscribe(res=>{
      this.processProjectDetailPeriodReport(res);
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    });
  }

  getProjectWiseEmpDetailsReport(project_code:any){
    this.managerService.getProjectWiseEmpDetailsReport(project_code.project_code).subscribe(res=>{
      this.projectWiseEmpDetailsReport=res?.data;
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    });
  }

  getEmployeeProjectDurationReport(projectCode:string, durationDays:string ){
    this.managerService.getEmployeeProjectDurationReport(projectCode, durationDays).subscribe(res=>{
      if (res?.message) {
        const errMsg = res?.message; 
        this.messageService.add({ severity: 'error', summary: '', detail: errMsg });
        return;
      }
      this.employeeProjectDurationReport=res.employees;
    },(err: any) => {
      this.activatedRouterService.updateError(err, this.messageService)
    });
  }
  
  getEmployeeSummaryReport(apiRequest:any){
    this.managerService.getEmployeeSummaryReport(apiRequest).subscribe(res=>{
      this.employeeSummaryReport=res;
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    });
  }

  getEmployeeDetailReport(apiRequest:any){
    this.managerService.getEmployeeDetailReport(apiRequest).subscribe(res=>{
      //this.employeeDetailReport=res;
      this.processEmployeeDetailReport(res);
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    });
  }

  processProjectDetailReport(dataobj: any): void {
    if (dataobj && dataobj.length > 0) {
      let allRows: any[] = [];

  
      dataobj.forEach((data: { task_description: { task_group: any; budgeted_hours:any;  allocated_hours:any; worked_hours:any; phase_wise_utilization:any }[]; project_region: any; project_country: any; project_code: any; description: any; project_type: any; delivery_model: any; start_date: any; end_date: any; project_status: any; total_budgeted_hours:any; total_allocated_hours: any; total_worked_hours: any; billable_hours: any; non_billable_hours: any; utilization_percentage: any; }) => {
        if (data.task_description.length > 0) {
          let mappedRows = data.task_description.map((task: { task_group: any; budgeted_hours:any; allocated_hours:any; worked_hours:any; phase_wise_utilization:any}) => {
            return {
              project_region: data.project_region,
              project_country: data.project_country,
              project_code: data.project_code,
              description: data.description,
              project_type: data.project_type,
              delivery_model: data.delivery_model,
              start_date: data.start_date,
              end_date: data.end_date,
              project_status: data.project_status,
              task: task.task_group,
              // task: task.description,
              // total_allocated_hours: data.total_allocated_hours,
              // total_worked_hours: data.total_worked_hours,
              // billable_hours: data.billable_hours,
              budgeted_hours: task.budgeted_hours,
              total_allocated_hours: task.allocated_hours,
              total_worked_hours: task.worked_hours,
              billable_hours: data.project_code == 'RB001' ? '0' : task.worked_hours,
              non_billable_hours: data.non_billable_hours,
              utilization_percentage: task.phase_wise_utilization
              // utilization_percentage: data.utilization_percentage
            };
          });
          allRows = allRows.concat(mappedRows); 
        } else {
          allRows.push({ 
            project_region: data.project_region,
            project_country: data.project_country,
            project_code: data.project_code,
            description: data.description,
            project_type: data.project_type,
            delivery_model: data.delivery_model,
            start_date: data.start_date,
            end_date: data.end_date,
            project_status: data.project_status,
            task: '',
            total_budgeted_hours: data.total_budgeted_hours,
            total_allocated_hours: data.total_allocated_hours,
            total_worked_hours: data.total_worked_hours,
            billable_hours: data.billable_hours,
            non_billable_hours: data.non_billable_hours,
            utilization_percentage: data.utilization_percentage
          });
        }
      });
  
      this.projectDetailReport = allRows; 
    } else {
      this.projectDetailReport = dataobj;
    }
  }

  processProjectDetailPeriodReport(dataobj: any): void {
    if (dataobj && dataobj.length > 0) {
      let allRows: any[] = [];

  
      dataobj.forEach((data: { task_description: { 
        task_group: any; budgeted_hours:any;  allocated_hours:any; worked_hours:any; phase_wise_utilization:any; total_allocated_hours_periodwise:any; total_worked_hours_periodwise:any; utilization_periodwise:any; start_date: any; end_date: any}[];
         project_region: any; project_country: any; project_code: any; description: any; project_type: any; delivery_model: any; start_date: any; end_date: any; project_status: any; total_budgeted_hours:any; total_allocated_hours: any; total_worked_hours: any; billable_hours: any; non_billable_hours: any; utilization_percentage: any; month_year:any; 
        }) => {
        if (data.task_description.length > 0) {
          let mappedRows = data.task_description.map((task: { task_group: any; budgeted_hours:any; allocated_hours:any; worked_hours:any; phase_wise_utilization:any; total_allocated_hours_periodwise:any; total_worked_hours_periodwise:any; utilization_periodwise:any; start_date: any; end_date: any}) => {
            return {
              project_region: data.project_region,
              project_country: data.project_country,
              project_code: data.project_code,
              description: data.description,
              project_type: data.project_type,
              delivery_model: data.delivery_model,
              start_date: data.start_date,
              end_date: data.end_date,
              project_status: data.project_status,
              task: task.task_group,
              budgeted_hours: task.budgeted_hours,
              total_allocated_hours: task.allocated_hours,
              total_worked_hours: task.worked_hours,
              billable_hours: data.project_code == 'RB001' ? '0' : task.worked_hours,
              non_billable_hours: data.non_billable_hours,
              utilization_percentage: task.phase_wise_utilization,
              total_allocated_hours_periodwise: task.total_allocated_hours_periodwise,
              total_worked_hours_periodwise: task.total_worked_hours_periodwise,
              utilization_periodwise: task.utilization_periodwise,
              phase_start_date: task.start_date,
              phase_end_date: task.end_date,
              month_year: data.month_year,
            };
          });
          allRows = allRows.concat(mappedRows); 
        } else {
          allRows.push({ 
            project_region: data.project_region,
            project_country: data.project_country,
            project_code: data.project_code,
            description: data.description,
            project_type: data.project_type,
            delivery_model: data.delivery_model,
            start_date: data.start_date,
            end_date: data.end_date,
            project_status: data.project_status,
            task: '',
            total_budgeted_hours: data.total_budgeted_hours,
            total_allocated_hours: data.total_allocated_hours,
            total_worked_hours: data.total_worked_hours,
            billable_hours: data.billable_hours,
            non_billable_hours: data.non_billable_hours,
            utilization_percentage: data.utilization_percentage
          });
        }
      });
  
      this.projectDetailPeriodReport = allRows; 
    } else {
      this.projectDetailPeriodReport = dataobj;
    }
  }

  processEmployeeDetailReport(dataobj: any[]): void {
    if (dataobj && dataobj.length > 0) {
      let allRows: any[] = []; 
  
      dataobj.forEach((data: {
        employee_name: string,
        country: string,
        project_region: string,
        project_country: string,
        project_code: string,
        description: string,
        project_type: string,
        delivery_model: string,
        start_date: string,
        end_date: string,
        project_status: string,
        task_description: {
          task_code: number,
          task_group: string,
          description: string,
          billable: string,
          start_date: string,
          end_date: string,
          allocated_hours: number,
          till_allocated_hours: number,
          worked_hours: number,
          till_utilization: number
        }[],
        total_allocated_hours: number,
        total_worked_hours: number,
        billable_hours: number,
        non_billable_hours: number,
        utilization_percentage: number
      }) => {
        if (data.task_description && data.task_description.length > 0) {
          let mappedRows = data.task_description.map((task: {start_date: string; end_date: string; task_group:string; allocated_hours:number; till_allocated_hours: number; worked_hours:number; till_utilization:number }) => {
            return {
              employee_name: data.employee_name,
              country: data.country,
              project_region: data.project_region,
              project_country: data.project_country,
              project_code: data.project_code,
              description: data.description,
              project_type: data.project_type,
              delivery_model: data.delivery_model,
              start_date: task.start_date,
              end_date: task.end_date,
              project_status: data.project_status,
              task: task.task_group,
              total_allocated_hours: task.allocated_hours,
              till_allocated_hours: task.till_allocated_hours,
              total_worked_hours: task.worked_hours,
              billable_hours: data.project_code == 'RB001' ? '0' : task.worked_hours,
              non_billable_hours: data.non_billable_hours,
              till_utilization: task.till_utilization
            };
          });
          allRows = allRows.concat(mappedRows);
        } 
        else {
          allRows.push({
            employee_name: data.employee_name,
            country: data.country,
            project_region: data.project_region,
            project_country: data.project_country,
            project_code: data.project_code,
            description: data.description,
            project_type: data.project_type,
            delivery_model: data.delivery_model,
            start_date: data.start_date,
            end_date: data.end_date,
            project_status: data.project_status,
            task_description: '',
            total_allocated_hours: data.total_allocated_hours,
            total_worked_hours: data.total_worked_hours,
            billable_hours: data.billable_hours,
            non_billable_hours: data.non_billable_hours,
            utilization_percentage: data.utilization_percentage
          });
        }
      });
  
      this.employeeDetailReport = allRows; 
    } else {
      this.employeeDetailReport = dataobj; 
  }

}

}
