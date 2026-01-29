import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, OnInit, ViewChild } from '@angular/core';
import { FormBuilder, FormControl, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { MessageService } from 'primeng/api';
import { ButtonModule } from 'primeng/button';
import { DropdownModule } from 'primeng/dropdown';
import { IconFieldModule } from 'primeng/iconfield';
import { InputTextModule } from 'primeng/inputtext';
import { Table, TableModule } from 'primeng/table';
import { ToastModule } from 'primeng/toast';
import { ActivatedRouterService } from 'src/app/services/activated-router-service';
import {PMOService} from 'src/app/services/pmo.service';
import { ManagerService} from 'src/app/services/manager.service';
import { TabViewModule } from 'primeng/tabview';
import { MasterDataService } from 'src/app/services/master-data.service';
import { CheckboxModule } from 'primeng/checkbox';

interface TimesheetEntry {
  id: number;
  task_description: string;
  month: number;
  year: number;
  date: string; // Assuming date is in "YYYY-MM-DD" format
  description: string;
  project_role: string;
  allocated_hours: number;
  booked_hours: number;
  worked_hours: string; // Assuming time is in "HH:MM:SS" format
  remarks: string;
  status: string;
  employee_code: string;
  project_code: string;
  comments:string;
}

interface ProjectTimesheet {
  project_code: string;
  project_description: string;
  budgeted_hours: number;
  allocated_hours: number;
  total_worked_hours: number;
  timesheet_entries: TimesheetEntry[];
}
@Component({
  selector: 'app-timesheet-approval',
   imports: [ReactiveFormsModule, ToastModule, CommonModule, DropdownModule, ButtonModule,
          InputTextModule, TableModule, FormsModule, IconFieldModule, TabViewModule, CheckboxModule],
  standalone:true,
  templateUrl: './timesheet-approval.component.html',
  styleUrls: ['./timesheet-approval.component.scss'],
  providers: [MessageService],
})
export class TimesheetApprovalComponent implements OnInit{
  @ViewChild('dt1') dt : Table | undefined
  timesheetApprovalForm!: FormGroup;
  statusList:any[]=[];
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
  managerTimesheetData:any[]=[];
  projects:any[]=[];
  projectTimesheet:ProjectTimesheet;
  projectHours:any = [];
  allPhases:any = [];
  currentEmpName:string = '';
  selectAll: boolean = false;
  employeeDetails:any[]=[];
  roles:any = [];
  userType:string = '';
  employeeId:string = '';
  showTimesheets:boolean = false;
  dataLoaded: boolean = false;
  isProjectsLoading: boolean = true;
  isEmpDetailsLoading: boolean = true;

  constructor(private router: Router,private formBuilder: FormBuilder,private managerService:ManagerService,
      private activatedRouterService: ActivatedRouterService,private messageService:MessageService,private cdr: ChangeDetectorRef,
    private pmoService:PMOService, private masterDataService:MasterDataService){
      this.projectTimesheet = {
        project_code: '-',
        project_description:'-',
        budgeted_hours: 0,
        allocated_hours: 0,
        total_worked_hours: 0,
        timesheet_entries: []
      };
  }
  ngOnInit(): void {
    this.employeeId = localStorage.getItem('userId') || '';
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
    //             (this.roles.includes('DeliveryHead') && this.roles.includes('Manager')) ||  
    //             (this.roles.includes('DeliveryHead') && this.roles.length === 1) ) {
    //               this.userType = 'DeliveryHead';

    // } else if ( (this.roles.includes('Management') && this.roles.includes('PMO')) ||
    //             (this.roles.includes('Management') && this.roles.includes('Employee')) || 
    //             (this.roles.includes('Management') && this.roles.includes('Manager')) || 
    //             (this.roles.includes('Management') && this.roles.length === 1) ) {
    //               this.userType = 'Management';
    // }    

    this.statusList=[
      {"name":"Open","value":"open"},
      {"name":"Approved","value":"approved"},
      {"name":"Rejected","value":"rejected"},
    ]
    this.getAllEmployees();
    this.buildForm();
    this.generateYearArray();
    // this.getProjects();
    const today = new Date();
    this.timesheetApprovalForm.controls['month'].setValue(today.getMonth() + 1); 
    this.timesheetApprovalForm.controls['year'].setValue(today.getFullYear());
    this.timesheetApprovalForm.controls['status'].setValue('open');

    this.masterDataService.getTasks().subscribe((res:any) => {
      this.allPhases = res?.['data'];
    })
  }

  buildForm(){
        this.timesheetApprovalForm = this.formBuilder.group({
          project_code: new FormControl('', [Validators.required]),
          employee_code: new FormControl(''),
          status: new FormControl(''),
          month: new FormControl('', [Validators.required, Validators.email]),
          year: new FormControl(null, [Validators.required]),
      });
    }
  
    getFormControl(formControlName:string) {
      return this.timesheetApprovalForm.get(formControlName);
    }
  
    getFormValidation() {
      const controls = this.timesheetApprovalForm.controls;  
      const basicFieldsValid =  controls['project_code'].value &&
                                controls['month'].value &&
                                controls['year'].value
      return basicFieldsValid;
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
        this.timesheetApprovalForm?.get('year')?.setValue(this.selectedYear);
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

      console.log('timesheet approval userType determined as:', this.userType, 'from roles:', this.roles);
    }


  //   getProjects(){
  //     console.log("userType is - ", this.userType);
  //     this.isProjectsLoading = true;
  //     this.pmoService.getProjects().subscribe(res=>{
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
  //       // console.log("this.projects after -", this.projects);
  //       // console.log("this.currentEmpName -", this.currentEmpName);
  //       this.projects = this.projects.map((project:any) => ({
  //         ...project,
  //         formattedLabel: `${project.project_description} - ${project.project_code}`  // Concatenating code & name
  //       }));
  //       this.projects.sort((a:any, b:any) => a.project_description.localeCompare(b.project_description));
  //       this.isProjectsLoading = false;
  //     },(err: any) => {
  //       this.isProjectsLoading = false; 
  //       this.activatedRouterService.updateError(err, this.messageService)
  //    })
  //  }

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

   getProjects() {
    console.log("timesheet approval userType is - ", this.userType);
    this.isProjectsLoading = true;

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
        this.isProjectsLoading = false;
      },
      (err: any) => {
        this.isProjectsLoading = false;
        this.activatedRouterService.updateError(err, this.messageService);
      }
    );
  }

    getAllEmployees(){
      this.isEmpDetailsLoading = true;
      this.masterDataService.getEmployeeDetails().subscribe(res=>{
        this.employeeDetails=res['data'].map((emp: { employee_code: any; name: any; }) => ({
          ...emp,
          employee_codewithName: `${emp.employee_code} - ${emp.name}`
        }));
        this.employeeDetails = this.employeeDetails.sort((a,b) => a.employee_code.localeCompare(b.employee_code));
       const employees = res['data'];
       const userId = localStorage.getItem('userId');
       const empObj = employees.find((emp:any) => emp.employee_code === userId);
       this.currentEmpName = empObj.name;
       console.log('this.currentEmpName:::',this.currentEmpName);
       this.isEmpDetailsLoading = false;
       this.getProjects();
     },(err: any) => {
        this.isEmpDetailsLoading = false; 
       this.activatedRouterService.updateError(err, this.messageService)
     })
   }
   
   getTimesheetProjectCode() {
    this.getPhasesByProject();
    const apiRequest = {
      "employee_code": this.timesheetApprovalForm.controls['employee_code']?.value == null ? "" : this.timesheetApprovalForm.controls['employee_code']?.value,
      "project_code": this.timesheetApprovalForm.controls['project_code']?.value == null ? "" : this.timesheetApprovalForm.controls['project_code']?.value,
      "month": this.timesheetApprovalForm.controls['month']?.value,
      "year": this.timesheetApprovalForm.controls['year']?.value,
      "status": this.timesheetApprovalForm.controls['status']?.value,
    };
    this.managerService.getTimesheetProjectCode(apiRequest).subscribe(
      (res) => {
        this.projectTimesheet=res;
         this.projectTimesheet.project_code=this.timesheetApprovalForm.controls['project_code']?.value;
         this.projectTimesheet.project_description=this.projects.find(p=>p.project_code===this.timesheetApprovalForm.controls['project_code']?.value).project_description;
      
          // Ensure default value for 'open' status is 'approved'
          this.projectTimesheet.timesheet_entries = this.projectTimesheet.timesheet_entries.map(timesheetData => ({
            ...timesheetData,
            selected: false,
            status: timesheetData.status === 'open' ? 'approved' : timesheetData.status // Set default to "approved" for "open"
          }));

          this.projectTimesheet.timesheet_entries = this.projectTimesheet.timesheet_entries.filter((entry:any) => {
            const roles = entry.role_name;
            const projectCode = entry.project_code;

            if (this.userType === 'HR') {
              return projectCode === 'RB001';
            }

            if (this.userType === 'Manager') {
              return (
                projectCode !== 'RB001' &&                // exclude HR project
                !roles.includes('DeliveryHead') &&        // manager cannot see DH
                !roles.includes('Management')             // manager cannot see MGT
                // !roles.includes('Manager')             // manager cannot see Manager
              );
            }

            if (this.userType === 'DeliveryHead') {
              return (
                projectCode !== 'RB001' &&                // exclude HR project
                !roles.includes('Management')             // DH should not see MGT
              );
            }

            if (this.userType === 'Management') {
              // Management can see EVERYTHING
              return true;
            }

            return entry
          });

          this.dataLoaded = true;
      },
      (err: any) => {
        this.dataLoaded = true;
        this.activatedRouterService.updateError(err, this.messageService);
      }
    );

    // Show the timesheet data table
    this.showTimesheets = true;

    // Optional: Scroll into view
    setTimeout(() => {
      const tableSection = document.getElementById('employeeTimesheets');
      if (tableSection) {
        tableSection.scrollIntoView({ behavior: 'smooth' });
      }
    }, 1000);
  }

  getPhasesByProject() {
    const payload = {
      "project_code": this.timesheetApprovalForm.controls['project_code']?.value
    }
    this.managerService.getPhasesByProjectCode(payload).subscribe((res:any) => {
      this.projectHours = res?.data || [];
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  getPhaseName(task_code: string) {
    const phase = this.allPhases.find((phase:any) => phase.task_code === task_code);
    return phase ? phase.task_group : ''
 }

  onChangeProjectCode(){
    // this.projectTimesheet.project_code=this.timesheetApprovalForm.controls['project_code']?.value;
    // this.projectTimesheet.project_description=this.projects.find(p=>p.project_code===this.timesheetApprovalForm.controls['project_code']?.value).project_description;
  }

  toggleSelectAll(event: any) {
    const select = event.checked;
    this.projectTimesheet.timesheet_entries.forEach((entry:any) => {
      entry.selected = select;
    });
  }

  isWeekend(dateString: string): boolean {
    const date = new Date(dateString);
    const day = date.getDay(); // Sunday = 0, Saturday = 6
    return day === 0 || day === 6;
  }

  applyFilterGlobal($event:any, stringVal:any) {
    this.dt!.filterGlobal(($event.target as HTMLInputElement).value, stringVal);
  }
  

  timesheetApproval() {
    const timesheetEntries = this.projectTimesheet.timesheet_entries;
    let mappedTimesheetEntriesList: any[] = [];
    let isValid = true;
  
    const selectedEntries = timesheetEntries.filter((entry:any) => entry.selected);
  
    if (selectedEntries.length === 0) {
      this.messageService.add({
        severity: 'error',
        summary: 'Validation Error',
        detail: 'Please select at least one record.'
      });
      return;
    }
  
    this.projectTimesheet.timesheet_entries = timesheetEntries.map((entry:any) => {
      if (entry.selected) {
        const status = entry.status ? entry.status.toLowerCase() : '';
        const hasComment = entry.comments && entry.comments.trim() !== '';
  
        // Check for validation
        if (status === 'rejected' && !hasComment) {
          isValid = false;
          return { ...entry, showCommentError: true };
        }
  
        // Valid entry — prepare data for backend
        if (status === 'approved' || status === 'rejected') {
          mappedTimesheetEntriesList.push({
            status: entry.status,
            comments: hasComment ? entry.comments : '',
            project_code: entry.project_code,
            employee_code: entry.employee_code,
            timesheet_id: entry.id
          });
        }
      }
      return { ...entry, showCommentError: false };
    });
  
     // If validation fails, block submission
    if (!isValid) {
      this.messageService.add({
        severity: 'error',
        summary: 'Validation Error',
        detail: 'Please enter comments for all rejected entries.'
      });
      return;
    }
  
    // Submit if valid
    if (mappedTimesheetEntriesList.length > 0) {
      this.managerService.timesheetApproval(mappedTimesheetEntriesList).subscribe(
        (data: any) => {
          this.messageService.add({ severity: 'success', summary: '', detail: data?.message });
  
          setTimeout(() => {
            const currentRoute = this.router.url;
            this.router.navigateByUrl('/', { skipLocationChange: true }).then(() => {
              this.router.navigateByUrl(currentRoute);
            });
          }, 500);
        },
        (err: any) => {
          this.activatedRouterService.updateError(err, this.messageService);
        }
      );
    }
  }  

  rejected(rowIndex: number, value: string) {
    // Update the specific row in the timesheet_entries array based on the rowIndex
    this.projectTimesheet.timesheet_entries = this.projectTimesheet.timesheet_entries.map((timesheetData, index) => {
      if (index === rowIndex) {
        return { ...timesheetData, status: value }; // Create a new object and update status
      }
      return timesheetData;
    });
  }
  approved(rowIndex:number,value:string){
    this.projectTimesheet.timesheet_entries = this.projectTimesheet.timesheet_entries.map((timesheetData, index) => {
      if (index === rowIndex) {
        return { ...timesheetData, status: value }; // Create a new object and update status
      }
      return timesheetData;
    });
  }

  updateStatus(rowIndex: number, value: string) {
    this.projectTimesheet.timesheet_entries = this.projectTimesheet.timesheet_entries.map((timesheetData, index) => {
      if (index === rowIndex) {
        return { ...timesheetData, status: value }; // Update status dynamically
      }
      return timesheetData;
    });
  }
  
  onCommentChange(entry: any) {
    if (entry.status?.toLowerCase() === 'rejected' && entry.comments?.trim()) {
      entry.showCommentError = false;
    }
  }
}
