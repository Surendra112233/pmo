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
import { ManagerService} from 'src/app/services/manager.service';
import { HrEmpReportComponent } from './hr-emp-report/hr-emp-report.component';
import { LoginService } from 'src/app/services/login.service';

@Component({
  standalone: true,
  selector: 'app-hr-reports',
  templateUrl: './hr-reports.component.html',
  styleUrls: ['./hr-reports.component.scss'],
  imports: [ReactiveFormsModule, ToastModule, CommonModule, DropdownModule, ButtonModule,
            InputTextModule, TableModule, FormsModule, IconFieldModule,MultiSelectModule, HrEmpReportComponent],
    providers:[MessageService]
})
export class HrReportsComponent implements OnInit {

  employeeReportForm!:FormGroup;
  projectType:any[]=[
     {name:"Employee Summary"},
     {name:"Employee Summary - Project Wise"},
     { name:"Employee Detailed"},
     { name:"Missed Entries Report"},
  ];
projects:any[]=[];
isProjectsLoading:boolean = true;
employeeDetails:any[]=[];
isEmpDetailsLoading:boolean = true;
isProjectCode:boolean=false;
isEmployeeCode:boolean=false;
employeeDetailReport:any[]=[];
employeeSummaryReport:any[]=[];
employeeSummaryProjectWiseReport:any[]=[];
missedEntriesReport:any[]=[];
reportType:string = '';

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
];
selectedYear: number=new Date().getFullYear();
years: number[] = [];
countryList: any = [];
roles:any = [];
userId:string = '';
employeeDropdownDisabled:boolean = false;

  
constructor(
  private formBuilder: FormBuilder,
  private pmoService:PMOService,
  private masterDataService:MasterDataService,
  private activatedRouterService: ActivatedRouterService,
  private messageService:MessageService,
  private managerService:ManagerService,
  private loginService:LoginService
  ){}

  ngOnInit(): void {
    this.roles = localStorage.getItem('Roles') || '';
    this.roles = this.roles.split(',');
    this.userId = localStorage.getItem('userId') || '';

    this.buildForm();
    this.generateYearArray();
    this.getProjects();
    this.getEmployees();
    this.getDropdownData();
    
    const today = new Date();
    this.employeeReportForm.controls['month'].setValue(today.getMonth() + 1); 
    this.employeeReportForm.controls['year'].setValue(today.getFullYear());
  }

 buildForm(){
      this.employeeReportForm = this.formBuilder.group({
        report_type: new FormControl('', [Validators.required]),
        project_code: new FormControl(null),
        employee_code: new FormControl(null),
        country: new FormControl(null),
        month: new FormControl(''),
        year: new FormControl(null),
    });
  }

  getProjects(){
      this.isProjectsLoading = true;
      this.pmoService.getProjects().subscribe(res=>{
        //display projects that are assigned to the current user
        this.projects = res['data']
        .filter((project:any)=>{
          return project.project_status == 'active'
        });
       
        this.projects = this.projects.map((project:any) => ({
          ...project,
          formattedLabel: `${project.project_description} - ${project.project_code}`  // Concatenating code & name
        }));
        this.projects.sort((a:any, b:any) => a.project_description.localeCompare(b.project_description));
        this.isProjectsLoading = false;
      },(err: any) => {
        this.isProjectsLoading = false; 
        this.activatedRouterService.updateError(err, this.messageService)
     })
   }

 getEmployees(){
  this.isEmpDetailsLoading = true;
  this.masterDataService.getEmployeeDetails().subscribe(res=>{
    this.employeeDetails=res['data'].map((emp: { employee_code: any; name: any; }) => ({
      ...emp,
      employee_codewithName: `${emp.employee_code} - ${emp.name}`
    }));
    this.employeeDetails = this.employeeDetails.sort((a,b) => a.employee_code.localeCompare(b.employee_code))

    this.isEmpDetailsLoading = false;
    if (this.roles.includes('Employee') && this.roles.length === 1) {     
      this.employeeDropdownDisabled = true;
      this.employeeReportForm.controls['employee_code']?.setValue(this.userId);
    } else {
      this.employeeDropdownDisabled = false;
    }
  },(err: any) => {
    this.isEmpDetailsLoading = false; 
    this.activatedRouterService.updateError(err, this.messageService)
  })
 }

 onChangeReportType(event:any){
    // this.isEmployeeCode=true;
    this.reportType = event.target.value;
    if(this.reportType === 'Missed Entries Report') {
      this.isProjectCode = true;
      this.isEmployeeCode = false;
    } else {
      this.isProjectCode = false;
      this.isEmployeeCode = true;
    }
    // this.employeeReportForm.controls['employee_code'].setValidators([Validators.required]);
    // this.employeeReportForm.controls['employee_code']?.setValue('');
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
    this.employeeReportForm?.get('year')?.setValue(this.selectedYear);
  }
}

getDropdownData(){
  this.loginService.getDropdownData().subscribe(data => {
    this.countryList=data.countryList;
  });
}

  onSubmit(){
    this.employeeDetailReport=[];
    this.employeeSummaryReport=[];
    this.employeeSummaryProjectWiseReport=[];
    this.missedEntriesReport=[];
    this.reportType = this.employeeReportForm.controls['report_type']?.value;
    
    if(this.reportType != 'Missed Entries Report'){
      let apiRequest = {
        "employee_code": this.employeeReportForm.controls['employee_code']?.value == null ? "" : this.employeeReportForm.controls['employee_code']?.value,
        "country": this.employeeReportForm.controls['country']?.value == null ? "" : this.employeeReportForm.controls['country']?.value,
        "month": this.employeeReportForm.controls['month']?.value,
        "year": this.employeeReportForm.controls['year']?.value,
      };
      

      if(this.employeeReportForm.controls['report_type']?.value =='Employee Summary'){
        this.getEmployeeSummaryReport(apiRequest);
      }  else if(this.employeeReportForm.controls['report_type']?.value =='Employee Summary - Project Wise'){
        this.getEmployeeSummaryProjectWiseReport(apiRequest);
      } else if(this.employeeReportForm.controls['report_type']?.value =='Employee Detailed'){
          this.getEmployeeDetailReport(apiRequest);
      }

    } else {
      const payload = {
        project_codes : this.employeeReportForm.controls['project_code']?.value == null ? "" : this.employeeReportForm.controls['project_code']?.value,
      }
      this.getMissedEntriesReport(payload);
    }
  }

  getFormControl(formControlName:string) {
    return this.employeeReportForm.get(formControlName);
  }

  getEmployeeSummaryReport(apiRequest:any){
    this.masterDataService.getEmployeeSummaryReport(apiRequest).subscribe(res=>{
      this.employeeSummaryReport=res['summary_report'];
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    });
  }

  getEmployeeSummaryProjectWiseReport(apiRequest:any){
    this.masterDataService.getEmployeeSummaryProjectWiseReport(apiRequest).subscribe(res=>{
      this.employeeSummaryProjectWiseReport=res['detailed_report_project'];
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    });
  }

  getEmployeeDetailReport(apiRequest:any){
    this.masterDataService.getEmployeeDetailReport(apiRequest).subscribe(res=>{
      this.employeeDetailReport=res['detailed_report'];
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    });
  }
  
  getMissedEntriesReport(apiRequest:any){
    this.masterDataService.getMissedEntriesReport(apiRequest).subscribe(res=>{      
      this.missedEntriesReport=res;
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    });
  }
}
