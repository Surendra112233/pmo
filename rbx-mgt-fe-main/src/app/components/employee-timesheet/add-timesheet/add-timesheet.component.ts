import { Component, OnInit,ChangeDetectorRef, ViewChild, ElementRef } from '@angular/core';
import { AbstractControl, FormBuilder, FormControl, FormGroup, FormsModule, ReactiveFormsModule, ValidationErrors, ValidatorFn, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { ConfirmationService, MessageService } from 'primeng/api';
import { CalendarModule } from 'primeng/calendar';
import { DropdownModule } from 'primeng/dropdown';
import { ToastModule } from 'primeng/toast';
import { Table, TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { EmployeeService } from '../../../services/employee.service';
import { ActivatedRouterService } from '../../../services/activated-router-service';
import { DialogModule } from 'primeng/dialog';
import { IconFieldModule } from 'primeng/iconfield'; 
import { PMOService } from '../../../services/pmo.service';
import { MasterDataService } from '../../../services/master-data.service';
import { MultiSelectModule } from 'primeng/multiselect';
import { AlphanumericDirective } from 'src/app/directives/alphanumeric.directive';
import { NoSpaceDirective } from 'src/app/directives/no-space.directive';
import { LoginService} from '../../../services/login.service';
import{TimeFormatPipe} from'../../../validators/time-format.pipe';
import { TabViewModule } from 'primeng/tabview';
import { max } from 'moment';

export function timeGreaterThanZeroValidator(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const value = control.value;

    // If value is a string or number, attempt to convert it to HH:mm format
    if (typeof value === 'string' || typeof value === 'number') {
      const valueStr = value.toString().trim();

      // Handle numeric values (e.g., 123 should be interpreted as "02:03")
      if (!valueStr.includes(':')) {
        const numValue = Number(valueStr);
        if (isNaN(numValue)) {
          return { invalidTime: true }; // Invalid number
        }

        // Convert the number to HH:mm format
        const hours = Math.floor(numValue / 60);
        const minutes = numValue % 60;
        const formattedTime = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
        return validateTimeFormat(formattedTime);
      }

      // Handle time strings like "02:30", "2:30", "03:15", etc.
      return validateTimeFormat(valueStr);
    }
    // If value is a Date object, extract hours and minutes and convert to HH:mm format
    else if (value instanceof Date) {
      const hours = value.getHours();
      const minutes = value.getMinutes();
      const formattedTime = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
      return validateTimeFormat(formattedTime);
    }
    // If value is null or undefined, treat it as invalid
    else {
      return { invalidTime: true };
    }
  };

  // Helper function to validate the time format (HH:mm)
  function validateTimeFormat(time: string): ValidationErrors | null {
    // Split the time string into hours and minutes
    const [hours, minutes] = time.split(':').map(Number);

    // Validate the time to ensure it's a valid time format and not 00:00
    if (isNaN(hours) || isNaN(minutes) || (hours === 0 && minutes === 0)) {
      return { invalidTime: true }; // Invalid time or 00:00
    }

    // No error, valid time
    return null;
  }
}


interface TimesheetEntry {
 id?:number;
  date: string;
  project_code: string;
  description: string;
  project_role: string;
  // allocated_hours: string;
  // booked_hours: string;
  task_description: number;
  task_descriptionValue:string;
  worked_hours: string;
  remarks: string;
  status: string;
  employee_code:string;
  employee_name?:string;
  designation?:string;
  month:number;
  year:number;
  new_description:string
}

@Component({
    selector: 'app-add-timesheet',
    imports: [ReactiveFormsModule, ToastModule, CalendarModule, CommonModule, DropdownModule, ButtonModule,
        InputTextModule, TableModule, FormsModule, DialogModule, IconFieldModule,MultiSelectModule,
        CalendarModule,NoSpaceDirective,AlphanumericDirective,TimeFormatPipe, TabViewModule],
    templateUrl: './add-timesheet.component.html',
    styleUrls: ['./add-timesheet.component.scss'],
    providers: [MessageService],
    standalone:true
})
export class AddTimesheetComponent implements OnInit{
  @ViewChild('dt2') dt : Table | undefined
  // @ViewChild('timesheetTable') timesheetTable !: ElementRef
  timesheetForm!: FormGroup;
  timesheetEntryForm!:FormGroup;
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
  employeeTimesheetData: TimesheetEntry[] = [];
  timesheetDataForAllEmployee: any[]=[];
  popupVisible: boolean = false;
  selectedTimesheet: TimesheetEntry | null = null;
  isRowHovered = false;
  isRowClicked = false;
  projectList:any[]=[];
  projectRoles:any[]=[];
  tasks:any[]=[];
  isTimesheetEdit:boolean=false;
  submittedProjectsMap: { [date: string]: string[] } = {};
  buttonValue:string='Save';
  screenType:string='Add';
  isNewEntry:boolean= false;
  isRejected:boolean= false;
  isApproved:boolean= false;
  employee_code:string='';
  time: Date = new Date();
  employee_name:string='';
  isTSAdmin:boolean=false;
  roles:string[]=[];
  hoursExceededError: boolean = false;
  highestBookedHours:string='';
  IsExceedeAllocatedHoursLimit:boolean=false;
  timesheetRowIndex:number=0;
  isWorkedHoursLimitPerDay:boolean=false;
  originalTimesheetData:any;
  projectHours:any;
  showProjectHours:boolean = false;
  allProjectPhases:any = [];
  allPhaseDescArray:any = [];
  projectCodePhasesMap:any = {};
  phaseNamesArray:any = [];
  isEmployeeActive:string='';
  disableProjectField:boolean = false;
  workedHrsDisabled:boolean = false;
  project_code:string = '';
  showTimesheetTable = false;
  employeeStatusLoaded = false;
  earlySubmitAttempted = false;
  showDesignation = false;
  employee_designation:string = '';
  employeeList:any = [];
  isEmpDetailsLoading:boolean = true;

  constructor(private router: Router,private formBuilder: FormBuilder,private employeeService:EmployeeService,
    private activatedRouterService: ActivatedRouterService,private messageService:MessageService,private loginService:LoginService,
    private pmoService:PMOService,private masterDataService:MasterDataService,private cdr:ChangeDetectorRef
  ){   }

  ngOnInit(): void {  
    this.buildForm();
    this.generateYearArray();
    this.getProjectRoles();
    this.getTasks();
    const today = new Date();
    this.timesheetForm.controls['month'].setValue(today.getMonth() + 1); 
    this.timesheetForm.controls['year'].setValue(today.getFullYear());
    
    const userId=localStorage.getItem("userId")||'';
    const Roles=localStorage.getItem('Roles')||'';
    if (Roles) {
      this.roles = Roles.split(',');
    }
    this.isTSAdmin = this.roles.some((role: string) => role.toLowerCase() === 'tsadmin');
    this.timesheetForm.controls['employee_code'].setValue(userId);

    this.getAllEmployees();
  }
  
  getAllEmployees() {
    this.isEmpDetailsLoading = true;
    this.masterDataService.getEmployeeDetails().subscribe((res:any)=> {
      this.employeeList = res?.['data'];      
      const currentEmployee = this.employeeList.find(
        (emp: any) => emp.employee_code === localStorage.getItem("userId")
      );

      if (currentEmployee) {
        this.isEmployeeActive = currentEmployee.status;
      } else {
        this.isEmployeeActive = '';
      }
      this.employeeStatusLoaded = true;

      // Show follow-up message only if user clicked submit too early
      if (this.earlySubmitAttempted) {
        this.messageService.add({ severity: 'success', summary: '', detail: 'Employee details loaded. Click on submit button to proceed.' });
        this.earlySubmitAttempted = false;
      }
      
      this.employeeList.sort((a:any, b:any) => a.employee_code.localeCompare(b.employee_code));
      this.employeeList = this.employeeList.map((emp:any) => ({
        ...emp,
        formattedLabel: `${emp.employee_code} - ${emp.name}`  // Concatenating code & name
      }));
      this.isEmpDetailsLoading = false;
    },(err: any) => {
       this.isEmpDetailsLoading = false; 
       this.activatedRouterService.updateError(err, this.messageService)
     })
  }

  getTotalPhases(employee: any): number {
    return employee.projects.reduce((total:any, project:any) => total + project.phases.length, 0);
  }  

  buildForm(){
      this.timesheetForm = this.formBuilder.group({
        employee_code: new FormControl('', [Validators.required,Validators.minLength(3),Validators.maxLength(10)]),
        month: new FormControl('', [Validators.required, Validators.email]),
        year: new FormControl(null, [Validators.required]),
    });
  }

  getProjectRoles(){
   this.masterDataService.getProjectRoles().subscribe(res=>{
    this.projectRoles=res['data'];
   })
  }

  getTasks(){
    this.masterDataService.getTasks().subscribe(res=>{
     this.tasks=res['data'];
    })
  }

  getProjectHrs() {
    const payload = {
      "employee_code": this.timesheetForm.controls['employee_code'].value
    }
    this.employeeService.getProjectHours(payload).subscribe(res=>{     
        this.projectHours = res?.data?.projects;
        this.projectCodePhasesMap = res?.data?.projects.reduce((acc:any, project:any) => {
          acc[project.project_code] = project.phases.map((phase:any)=>  ({
            // phase_id: 59,            
            phase_id: phase.phase_id,
            phase_name: phase.phase_name
          }));
          return acc;
        }, {});
        console.log("projectPhasesMap::::", this.projectCodePhasesMap);
        this.getTimesheetByEmployeeCode();
      }
    );
  }
  
  generateYearArray() {
    // const currentYear = new Date().getFullYear();
    // const startYear = 2025; //currentYear - 1;
    // const endYear = currentYear + 1;
    // for (let year = startYear; year <= endYear; year++) {
    //   this.years.push(year);
    // }

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
      this.timesheetForm?.get('year')?.setValue(this.selectedYear);
    }
  }

 
  getFormControl(formControlName:string) {
    return this.timesheetForm.get(formControlName);
  }

  getFormValidation() {
    const controls = this.timesheetForm.controls;  
    const basicFieldsValid =  controls['employee_code'].value &&
                              controls['month'].value &&
                              controls['year'].value
    return basicFieldsValid;
  }  

  getTimesheetFormValidation() {
    const controls = this.timesheetEntryForm.controls;  
    const basicFieldsValid =  controls['project_code'].value &&
                              controls['task_description'].value &&
                              controls['new_description'].value &&
                              controls['worked_hours'].value                              
    return basicFieldsValid;
  }  

  getTimesheetByEmployeeCode() {
    this.employee_code=this.timesheetForm.controls['employee_code'].value;
    const obj={
      "employee_code": this.timesheetForm.controls['employee_code'].value,
      "month": this.timesheetForm.controls['month'].value,
      "year": +this.timesheetForm.controls['year'].value
    };
    this.employeeService.getTimesheetByEmployeeCode(obj).subscribe(
      (res) => {
        this.timesheetDataForAllEmployee = res['data'];
        this.timesheetDataForAllEmployee = this.timesheetDataForAllEmployee.map(entry => {
          return {
            ...entry,
            date: this.formatToDDMMYY(entry.date)
          };
        });
        this.getProjectDetailsByEmployeeCode();
        //this.populateTimesheet(this.timesheetDataForAllEmployee);
      },
      (err: any) => {
        this.timesheetDataForAllEmployee=[];
        this.getProjectDetailsByEmployeeCode();
        this.activatedRouterService.updateError(err, this.messageService);
      }
    );
    this.populateTimesheet(this.timesheetDataForAllEmployee);
  }

  onSubmit(){
    if (!this.employeeStatusLoaded) {
      this.earlySubmitAttempted = true; 
      this.messageService.add({ severity: 'warn', summary: '', detail: 'Please wait, loading employee details...' });
      return;
    }

    if(this.isEmployeeActive == 'active') {
      //active employee only can add timesheet
      // this.getProjectHrs();
      // this.getTimesheetByEmployeeCode();
      this.buildTimesheetEntryForm();
      this.getProjectHrs();
      this.showProjectHours = true;

      // Show the timesheet data table
      this.showTimesheetTable = true;

      // Optional: Scroll into view
      setTimeout(() => {
        // const tableSection = document.getElementById('employeeTimesheetTable');
        // if (tableSection) {
        //   tableSection.scrollIntoView({ behavior: 'smooth' });
        // }
        // this.timesheetTable.nativeElement.scrollIntoView({ behavior: 'smooth' });
      }, 1000);
    } else {
      this.messageService.add({ severity: 'error', summary: '', detail: 'Inactive employee cannot add timesheet' }); 
    }

  }

  getProjectDetailsByEmployeeCode(){
    this.employeeService.getProjectDetailsByEmployeeCode(this.timesheetForm.get('employee_code')?.value).subscribe
    (res=>{
      this.employee_code=res.employee_code;
      this.employee_name=res.employee_name;
      this.employee_designation= res.employee_designation;
      this.projectList=res.projects;
      this.projectList = this.projectList.map((project:any) => ({
        ...project,
        formattedLabel: `${project.project_code} - ${project.description}`  // Concatenating code & name
      }));
      this.projectList.sort((a:any, b:any) => a.description.localeCompare(b.description));
      this.populateTimesheet(this.timesheetDataForAllEmployee);
    })
  }


  navigateToGrid(){
    this.router.navigate(['/emp/timesheet']);
  }

  formatToDDMMYY(dateStr: string): string {
    const date = new Date(dateStr);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0'); // Months are 0-based
    const year = String(date.getFullYear()); // Get last 2 digits
    // const year = String(date.getFullYear()).slice(-2); // Get last 2 digits
    return `${day}-${month}-${year}`;
  }
  
  populateTimesheet(timesheet: TimesheetEntry[]) {
    const selectedMonthIndex = this.timesheetForm.get('month')?.value;
    const selectedYear = this.timesheetForm.get('year')?.value;

    if (!selectedMonthIndex || !selectedYear) return;
    const daysInMonth = new Date(selectedYear, selectedMonthIndex, 0).getDate();
    this.employeeTimesheetData = [];

    // Create a map to store entries by date
    const timesheetMap = new Map<string, TimesheetEntry[]>();
    // console.log("timesheet - ", timesheet);
    
    timesheet.forEach((entry: TimesheetEntry) => {
      console.log("entry - ", entry);
        this.buildPhaseDropDownItems(entry.project_code);

        if (!timesheetMap.has(entry.date)) {
            timesheetMap.set(entry.date, []);
        }
        timesheetMap.get(entry.date)?.push({
            ...entry,
            // booked_hours:this.formatTimeToHHmm(entry.booked_hours),
            // task_descriptionValue: this.tasks.find(task => entry.task_description == task.task_code).description,
            // task_description:this.tasks.find(task => entry.task_description == task.task_code).task_code,
            project_role: entry.project_code == 'RB001' ? this.employee_designation : entry.project_role,
            task_descriptionValue: this.allProjectPhases.find((phase: any) => 
              String(phase.value) === String(entry.task_description)
            )?.name || '',
            task_description: this.allProjectPhases.find((phase: any) => 
              String(phase.value) === String(entry.task_description)
            )?.value || 0,
            employee_code:this.employee_code,
            employee_name:this.employee_name,
            month:+this.timesheetForm.get('month')?.value,
            year:+this.timesheetForm.get('year')?.value
        });
    });

    // Populate timesheet data ensuring empty rows for missing dates
    for (let index = 0; index < daysInMonth; index++) {
        // const currentDate = `${selectedYear}-${selectedMonthIndex.toString().padStart(2, '0')}-${(index + 1).toString().padStart(2, '0')}`;
        const currentDate = `${(index + 1).toString().padStart(2, '0')}-${selectedMonthIndex.toString().padStart(2, '0')}-${selectedYear.toString()}`;
        // const currentDate = `${(index + 1).toString().padStart(2, '0')}-${selectedMonthIndex.toString().padStart(2, '0')}-${selectedYear.toString().slice(-2)}`;
        
        const jsDate = new Date(`${selectedYear}-${selectedMonthIndex.toString().padStart(2, '0')}-${(index + 1).toString().padStart(2, '0')}`);
        const dayOfWeek = jsDate.getDay(); // 0 (Sun) to 6 (Sat)
        const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;

        if (timesheetMap.has(currentDate)) {
          const entries = timesheetMap.get(currentDate)!;
          entries.forEach((entry:any) => entry['isWeekend'] = isWeekend);
          this.employeeTimesheetData.push(...timesheetMap.get(currentDate)!);
        } else {
            this.employeeTimesheetData.push({
                date: currentDate,
                project_code: '',
                description: '',
                employee_name:this.employee_name,
                project_role: '',
                // allocated_hours: '',
                // booked_hours: '',
                worked_hours: '',
                task_description: 0,
                task_descriptionValue:'',
                remarks: '',
                status: '',
                employee_code:this.employee_code,
                month:+this.timesheetForm.get('month')?.value,
                year:+this.timesheetForm.get('year')?.value,
                new_description: '',
                isWeekend
            } as TimesheetEntry);
        }
    }
    // this.highestBookedHours = this.employeeTimesheetData .filter(emp => emp.status.toLowerCase() !== 'rejected').map(emp => emp.booked_hours).reduce((max, time) => (time > max ? time : max), '00:00');
}

getWeekendLabel(dateStr: string): string {
  // Assuming dateStr is in "dd-MM-yyyy" format
  const [day, month, year] = dateStr.split('-').map(Number);
  const dateObj = new Date(year, month - 1, day);
  const dayIndex = dateObj.getDay(); // 0 = Sunday, 6 = Saturday

  return dayIndex === 0 ? 'Sunday' : dayIndex === 6 ? 'Saturday' : 'Week Off';
}

buildPhaseDropDownItems(projectCode:string) {
  //build dropdown items for phase from here
  // console.log("projectCode::", projectCode);
  // console.log("this.projectCodePhasesMap::", this.projectCodePhasesMap);
  this.phaseNamesArray = this.projectCodePhasesMap[projectCode];
  // console.log(this.phaseNamesArray);
  // console.log(this.tasks);

  if(this.phaseNamesArray) {
    // Filter and map to required format
    this.allProjectPhases = this.phaseNamesArray.map((phaseName:any) => {
      return {name: phaseName.phase_name, value: phaseName.phase_id };
      // const match = this.tasks.find(item => item.task_group === phaseName.phase_id);
      // return match ? { name: phaseName, value: match.task_code } : null;
    })
    .filter(Boolean); //.filter(Boolean) removes any null values in case no match is found   
    // console.log("this.allProjectPhases:::", this.allProjectPhases);
    //till here
  }
}

showPopup(data: TimesheetEntry, rowIndex:number) {
  console.log('data 0:::', data);
  console.log('rowIndex:::', rowIndex);
  this.cdr.detectChanges();
  this.timesheetRowIndex=rowIndex;
  this.originalTimesheetData = JSON.parse(JSON.stringify(data)); console.log("this.originalTimesheetData:", this.originalTimesheetData)
  this.selectedTimesheet = data; // Assign the selected row data
 data.worked_hours=data.worked_hours ? data.worked_hours.slice(0,5):"";
  this.buildTimesheetEntryForm();
  this.timesheetEntryForm.controls['date'].setValue(data.date);
  
  // if(this.isNewEntry == true) {
  //   this.disableProjectField = false;
  // } else if(this.isNewEntry == false) {
  //   this.disableProjectField = true;
  // }
  if (data) {
    console.log("data::", data);

      if(data.task_description == 0) {
        //if there is no timesheet entered then do nothing
        this.allProjectPhases = [];
      } else {
        this.project_code = data.project_code;
        console.log("this.allProjectPhases before - ", this.allProjectPhases);
        this.buildPhaseDropDownItems(data.project_code);
        console.log("this.allProjectPhases after - ", this.allProjectPhases);  
        //get respective phase name for selected code
        const selectedPhaseName =  this.allProjectPhases
                                  .filter((phase:any) => data.task_descriptionValue == phase.name)
                                  .map((phase:any) => phase.name)

        //build dropdown items for task description column based on above phase name
        this.masterDataService.getPhasesWithDescription(this.project_code).subscribe(res => {
          this.allPhaseDescArray = res[selectedPhaseName[0]]?.map((item:any) => ({ name: item, value: item })) || [];
        })        
      }
      console.log('data 1::::', data)
      // setTimeout(() => {
        this.timesheetEntryForm.patchValue({
          id:data.id,
          date:data.date,
          project_code: data.project_code,
          description: data.description,
          project_role: data.project_role,
          // allocated_hours: data.allocated_hours,
          // booked_hours: +data.booked_hours,
          employee_name:this.employee_name,
          worked_hours: data.worked_hours ? this.formatTimeToHHmm(data.worked_hours):"",
          // task_descriptionValue: data.task_descriptionValue,
          // task_description:  this.tasks
          // .filter(task => data.task_descriptionValue.includes(task.description))
          // .map(task => task.task_code),
          task_descriptionValue: data.task_descriptionValue,
          task_description:  this.allProjectPhases
          .filter((phase:any) => data.task_descriptionValue == phase.name)
          .map((phase:any) => phase.value),
          remarks: data.remarks,
          status: data.status,
          new_description: data.new_description
          // new_description: this.allPhaseDescArray
          // .filter((desc:any) => data.new_description == desc.value)
          // .map((desc:any) => desc.value)
        });
      // }, 500)

  }
  
  if(this.timesheetEntryForm.controls['worked_hours'].value==""||this.timesheetEntryForm.controls['worked_hours'].value=="NaN"){
    const zeroTime = new Date();
      zeroTime.setHours(0, 0, 0, 0);
    this.timesheetEntryForm.controls['worked_hours'].setValue(zeroTime);
  }

  this.popupVisible = true;
  // this.buttonValue='Save';
  this.getProjectDropdown();
}

onRowHover(isHovered: boolean) {
  this.isRowHovered = isHovered;
}

onRowClick(isClicked: boolean) {
  this.isRowClicked = isClicked;
}
getTimesheetFormControl(formControlName:string) {
  return this.timesheetEntryForm.get(formControlName);
}

onChangeTask(event:any){
 this.timesheetEntryForm.get('task_description')?.setValue(event.target.value);
 this.getProjectDropdown();
}

getTimeWithoutSeconds(time: string): string {
  if (time && time.length === 8 && time.indexOf(":") === 2) {
      return time.slice(0, 5);  // Slice to get hh:mm
  }
  return time;  // If already in hh:mm format, return as is
}

buildTimesheetEntryForm(){
  this.timesheetEntryForm = this.formBuilder.group({
    id:new FormControl(''),
    date:new FormControl(''),
    project_code: new FormControl('', [Validators.required]),
    description: new FormControl(''),
    project_role: new FormControl(''),
    employee_name: new FormControl(''),
    // allocated_hours:new FormControl(''),
    // booked_hours: new FormControl(''),
    worked_hours: new FormControl('', [Validators.required,timeGreaterThanZeroValidator()]),
    task_description: new FormControl('', [Validators.required]),
    task_descriptionValue:new FormControl(''),
    remarks: new FormControl('', [Validators.maxLength(200)]),
    status: new FormControl('pending'),
    new_description: new FormControl('', [Validators.required])
    });
   
}
// applyFilterGlobal($event: any, stringVal: any) {
// }
 
convertDateFormat(dateStr:any) {
  const [day, month, year] = dateStr.split("-");
  return `${year}-${month}-${day.padStart(2, '0')}`;
}

saveTimesheetEntry() {
  const formData = this.timesheetEntryForm.value;
  const projectData = {
    id:formData?.id,
    date: formData.date,
    // date: this.convertDateFormat(formData.date),
    project_code: formData.project_code,
    description: formData.description,
    project_role: formData.project_role,
    // allocated_hours: formData.allocated_hours,
    // booked_hours: formData.booked_hours?this.formatTimeToHHmm(formData.booked_hours):"",
    worked_hours: this.formatTimeToHHmm(formData.worked_hours),
    // task_descriptionValue: this.tasks
    // .find(task => formData.task_description == task.task_code).description,
    task_descriptionValue: this.allProjectPhases
    .find((phase:any) => formData.task_description == phase.value).name,
    task_description:+formData.task_description,
    remarks: formData.remarks,
    status: formData.status,
    employee_code: this.employee_code,
    employee_name:this.employee_name,
    month: +this.timesheetForm.get('month')?.value,
    year: +this.timesheetForm.get('year')?.value,
    new_description: formData.new_description
  };

  this.submitTimesheetFromPopup(projectData);
    // Close the popup and reset the form
  this.popupVisible = false;
  this.selectedTimesheet = null;
  this.timesheetRowIndex=0;
  this.timesheetEntryForm.reset();
}

popuponClose(event:any){
  if (event && event.originalEvent && event.originalEvent.target && event.originalEvent.target.classList.contains('p-dialog-header-icon'))
     {
   this.loginService.showLoader();
   this.getTimesheetByEmployeeCode();
    setTimeout(() => {
      this.loginService.hideLoader();
    }, 1000);
    this.popupVisible = false;
    this.selectedTimesheet = null;
    this.timesheetRowIndex=0;
    this.timesheetEntryForm.reset();
  }
  else{
   
    this.selectedTimesheet = null;
    this.timesheetRowIndex=0;
    this.timesheetEntryForm.reset();
  }
  this.isNewEntry = false;
  this.isRejected = false;
  this.isApproved = false;
  this.allPhaseDescArray = [];

}
cancelTimesheet() { 
  this.loginService.showLoader();
  this.isNewEntry = false;
  this.isRejected = false;
  this.isApproved = false;
  this.allPhaseDescArray = [];
  this.getTimesheetByEmployeeCode();
  setTimeout(() => {
    this.loginService.hideLoader();
  }, 1000);
  this.popupVisible = false;
  this.selectedTimesheet = null;
  this.timesheetRowIndex=0;
  this.timesheetEntryForm.reset();
}

newEntry() {
  this.buttonValue = 'Save';
  this.screenType='Add';
  this.isNewEntry = true;
  this.isRejected = false;
  this.isApproved = false;
  this.allProjectPhases = [];
  this.allPhaseDescArray = [];
  this.disableProjectField = false;
  this.showDesignation = false;
  
  this.timesheetEntryForm.patchValue({
    id:undefined,
    description: '',
    project_code: '',
    project_role: '',
    worked_hours: "00:00",
    task_description: '',
    task_description_value: '',
    employee_name:this.employee_name,
    remarks: '',
    status: 'open',
    new_description: ''
  });
}

getProjectDropdown(){

  const formData = this.timesheetEntryForm.value;
  this.hoursExceededError = false;
  // const indexData = this.employeeTimesheetData.find((entry) => (entry.date === formData.date && entry.project_code === formData.project_code && entry.task_description==formData.task_description));
  const indexData = this.employeeTimesheetData.find((entry, index) => (index== this.timesheetRowIndex));
  // const latestBookedHours = this.employeeTimesheetData.map(emp => emp.booked_hours).reduce((max, time) => (time > max ? time : max), '00:00');
  // this.highestBookedHours=this.highestBookedHours<latestBookedHours?latestBookedHours:this.highestBookedHours;
  // //const indexToRemove = this.projectList.findIndex(project => project === indexData?.project_code);
  this.project_code = indexData?.project_code || '';

  this.buildPhaseDropDownItems(formData.project_code);
  console.log('this.employeeTimesheetData:::', this.employeeTimesheetData);
  console.log('indexData:::', indexData);
  console.log('formData:::', formData);
  

  if(this.isNewEntry == true) {
    this.disableProjectField = false;
    const matchedData = this.projectList.filter(project => project.project_code == formData.project_code);
    this.project_code = matchedData?.[0]?.project_code;
    this.showDesignation = matchedData?.[0]?.project_code === 'RB001';
    
    return this.timesheetEntryForm.patchValue({
      id: undefined,
      date:indexData?.date,
      project_code: matchedData?.[0]?.project_code,
      description: matchedData?.[0]?.description,
      project_role: matchedData?.[0]?.project_code === 'RB001' ? this.employee_designation : matchedData?.[0]?.project_role,
      employee_name:this.employee_name
    });
  }
  
  if(indexData?.project_code){console.log("getProjectDropdown update");
    this.buttonValue='Update';
    this.screenType='Edit';
    if(indexData.status == 'rejected') {
      this.isRejected = true;
    } else if (indexData.status == 'approved') {
      this.isApproved = true;
    }
    this.disableProjectField = true;
    indexData.worked_hours=indexData.worked_hours ? indexData.worked_hours.slice(0,5):"";
    this.timesheetEntryForm.patchValue({
        id:indexData?.id,
        date:indexData?.date,
        project_code: indexData?.project_code,
        description: indexData?.description,
        project_role: indexData?.project_role,
        // allocated_hours: indexData?.allocated_hours,
        // booked_hours: indexData?.booked_hours,
        employee_name:this.employee_name,
        worked_hours: indexData?.worked_hours ? this.formatTimeToHHmm(indexData?.worked_hours):"",
        task_descriptionValue:indexData?.task_descriptionValue,
        task_description: +indexData.task_description, // Assuming task_description is what you want
        remarks: indexData?.remarks,
        status: indexData?.status,
        new_description: indexData?.new_description
    });
 }
  else{console.log("getProjectDropdown save");
    this.buttonValue='Save';
    this.screenType='Add';
    this.disableProjectField = false;
    const projectData=this.projectList.find((project) => project.project_code === formData.project_code);
    this.highestBookedHours= this.highestBookedHours>projectData.total_worked_hours?this.highestBookedHours:projectData.total_worked_hours,
    projectData.total_worked_hours=projectData.total_worked_hours ? projectData.total_worked_hours.slice(0,5):"";

    this.timesheetEntryForm.patchValue({
      id:undefined,
      description: projectData.description,
      project_role: projectData.project_role,
      // allocated_hours: projectData.allocated_hours,
      // booked_hours: this.highestBookedHours,
      worked_hours: projectData.worked_hours ? this.formatTimeToHHmm(projectData.worked_hours) : "",
      // task_description: +formData.task_description, //to check again
      task_description: '',
      employee_name:this.employee_name,
      remarks: '',
      status: 'open',
      // new_description: formData.new_description //to check again
      new_description: ''
   });
   
   if(this.timesheetEntryForm.controls['worked_hours'].value==""||this.timesheetEntryForm.controls['worked_hours'].value=="NaN"){
      const zeroTime = new Date();
        zeroTime.setHours(0, 0, 0, 0);
      this.timesheetEntryForm.controls['worked_hours'].setValue(zeroTime);
    }
  }

  if(this.timesheetEntryForm.controls['project_code'].value == 'RB001') {
    this.showDesignation = true;
    this.timesheetEntryForm.patchValue({
      project_role: this.employee_designation,
    })
  } else {
    this.showDesignation = false;
  }

  this.isWorkedHoursLimitPerDay = false;
  this.IsExceedeAllocatedHoursLimit = false;
}

onTaskChange(event: any) {

  //get respective phase name for selected code
  const selectedPhaseName = this.allProjectPhases.find((phase:any) => phase.value == event.value).name;
  
  this.project_code = this.timesheetEntryForm.get('project_code')?.value;
  //build dropdown items for task description column based on above phase name
  this.masterDataService.getPhasesWithDescription(this.project_code).subscribe(res => {
    this.allPhaseDescArray = res[selectedPhaseName]?.map((item:any) => ({ name: item, value: item })) || [];
  })


  const formData = this.timesheetEntryForm.value;
  // this.buttonValue = 'Save';

  // project data matching the selected project code
  const projectData = this.projectList.find((project) => project.project_code === formData.project_code);

  // Update the highestBookedHours
  this.highestBookedHours = this.highestBookedHours > projectData.total_worked_hours ? this.highestBookedHours : projectData.total_worked_hours;
  projectData.total_worked_hours = projectData.total_worked_hours ? projectData.total_worked_hours.slice(0, 5) : "";

  // existing entry in employeeTimesheetData based on date, project code, and task description
  const existingEntryIndex = this.employeeTimesheetData.findIndex(
    entry => entry.date === formData.date && entry.project_code === formData.project_code && entry.task_description === event?.value
  );
    
  // If no matching entry exists,
  this.timesheetEntryForm.patchValue({
    // id: undefined, //commented bec when updating, if phase is changed from prepare --> deploy then due to this undefined id, add api is being called instead of update api
    description: projectData.description,
    project_role: projectData.project_code === 'RB001' ? this.employee_designation : projectData.project_role,
    // allocated_hours: projectData.allocated_hours,
    // booked_hours: this.highestBookedHours,
    worked_hours: "",
    task_description: +formData.task_description, 
    new_description: '', //to check again 
    // new_description: +formData.new_description, 
    employee_name: this.employee_name,
    remarks: '',
    status: 'open'
  });

  this.isWorkedHoursLimitPerDay = false;
  this.IsExceedeAllocatedHoursLimit = false;

  if(this.timesheetEntryForm.controls['worked_hours'].value==""||this.timesheetEntryForm.controls['worked_hours'].value=="NaN"||this.timesheetEntryForm.controls['worked_hours'].value=="undefined"){
    const zeroTime = new Date();
      zeroTime.setHours(0, 0, 0, 0);
    this.timesheetEntryForm.controls['worked_hours'].setValue(zeroTime);
  }
}

onTaskDescriptionChange(event: any) {
  this.workedHrsDisabled = false;
  const zeroTime = new Date();
  zeroTime.setHours(0, 0, 0, 0);
  this.timesheetEntryForm.controls['worked_hours'].setValue(zeroTime);
  // this.timesheetEntryForm.controls['worked_hours'].setValue('00:00');
  console.log('event.value:::', event.value)
  if(event.value == 'Holiday' || event.value == 'Client Holiday / Designated Holiday' || event.value == 'Full Day Leave' 
    || event.value == 'Full day leave' || event.value == 'Sick Leave') {
    this.timesheetEntryForm.controls['worked_hours'].setValue('08:00');
    this.workedHrsDisabled = true;
  } else if (event.value == 'Half Day Leave' || event.value == 'Half day leave') {
    this.timesheetEntryForm.controls['worked_hours'].setValue('04:00');
    this.workedHrsDisabled = true;
  }
}

submitTimesheetFromPopup(timesheetData:any){
  console.log("submitTimesheetFromPopup - timesheetData before:::", timesheetData)
  this.loginService.showLoader();

  //convert date from dd-mm-yyyy to yyyy-mm-dd
  const [dd, mm, yyyy] = timesheetData.date.split('-');
  timesheetData.date = `${yyyy}-${mm}-${dd}`;
  console.log("submitTimesheetFromPopup - timesheetData after:::", timesheetData)
  if(timesheetData?.id){
    let updatetimesheetData:any[]=[];
    updatetimesheetData.push(timesheetData);
    this.employeeService.updateTimesheet(updatetimesheetData).subscribe(
      (res:any)=>{ 
        this.messageService.add({ severity: 'success', summary: '', detail: res?.message });    
        this.getTimesheetByEmployeeCode();
        setTimeout(() => {
          this.loginService.hideLoader();
        }, 1000);
    },(err: any) => { 
      this.loginService.hideLoader();
      // console.log(err);
      // console.log('err', err, err.error[0].worked_hours)
      const errMsg = err?.error?.error || err?.error?.[0]?.worked_hours?.[0] || err?.error?.errors?.[0]?.worked_hours?.[0] || err?.error?.errors?.[0]?.date?.[0] || 'Total worked hours cannot exceed 8 hours per day';
      this.messageService.add({ severity: 'error', summary: '', detail: errMsg });
    });
    
  }
  else{

    let createtimesheetData:any[]=[];
    createtimesheetData.push(timesheetData);
    this.employeeService.saveTimesheet(createtimesheetData).subscribe(
        (res:any)=>{
          this.messageService.add({ severity: 'success', summary: '', detail: res?.message });

          //reflect entered popup details into timesheet after successfull save from here
          // Find all indices matching the selected date and project code
          const existingEntryIndex = this.employeeTimesheetData.findIndex(
            entry => (entry.date === timesheetData.date && entry.project_code === timesheetData.project_code && entry.task_description === timesheetData.task_description)
          );

          // if (existingEntryIndex !== -1) {
          //   // An entry with the same date and project code exists, update it
          //   this.employeeTimesheetData[existingEntryIndex] = timesheetData;
          // }
          //  else {
            // No entry exists for this date and project code
            // Find all indices matching the selected date
            const dateIndices = this.employeeTimesheetData
              .map((entry, index) => entry.date === timesheetData.date ? index : -1)
              .filter(index => index !== -1);

            if (dateIndices.length === 0) {
              // No entry exists for this date → insert a new row
              this.employeeTimesheetData.push(timesheetData);
            } else {
              // Check if any row is empty for that date
              const emptyRowIndex = dateIndices.find(index =>
                !this.employeeTimesheetData[index].project_code && !this.employeeTimesheetData[index].task_description
              );

              if (emptyRowIndex !== undefined) {
                // If an empty row exists, replace it
                this.employeeTimesheetData[emptyRowIndex] = timesheetData;
              } else {
                this.employeeTimesheetData.splice(dateIndices[dateIndices.length - 1] + 1, 0, timesheetData);
              }
            }
          // }
          //till here
          
          this.getTimesheetByEmployeeCode();
          setTimeout(() => {
            this.loginService.hideLoader();
          }, 1000);
      },(err: any) => {
        this.loginService.hideLoader();
        // console.log(err);
        // console.log(this.employeeTimesheetData);
        const errMsg = err?.error?.error || err?.error?.[0]?.worked_hours?.[0] || err?.error?.[0]?.date?.[0] || err?.error?.errors?.[0]?.date?.[0]
        this.messageService.add({ severity: 'error', summary: '', detail: errMsg });
      });
    } 
    this.isNewEntry = false;
}

submitTimesheet(){
  const timesheetData=this.employeeTimesheetData.filter(entry => entry.project_code !== null && entry.project_code !== '');
  let updateTimesheetList = timesheetData.filter(item => item.id);
  let createTimesheetList = timesheetData.filter(item => item.id === null || item.id === undefined);

  if(updateTimesheetList.length>0){
    this.employeeService.updateTimesheet(updateTimesheetList).subscribe(
      data=>{
      this.messageService.add({ severity: 'success', summary: '', detail: 'Timesheet Updated Successfully' });
      setTimeout(() => {
        this.navigateToGrid()
      }, 1000);
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    });
  }
  if(createTimesheetList.length>0){
  this.employeeService.saveTimesheet(createTimesheetList).subscribe(
      data=>{
      this.messageService.add({ severity: 'success', summary: '', detail: 'Timesheet Created Successfully' });
      setTimeout(() => {
        this.navigateToGrid()
      }, 1000);
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    });
    }
 
}

formatTimeToHHmm(date: any): string {
  // If the date is a string in HH:mm format, just return it
  if (typeof date === 'string') {
    return date;
  }

  // Check if the input is a valid Date object
  if (date instanceof Date && !isNaN(date.getTime())) {
    // Get the hours and minutes from the Date object
    const hours = date.getHours().toString().padStart(2, '0'); // Ensure 2 digits
    const minutes = date.getMinutes().toString().padStart(2, '0'); // Ensure 2 digits
    return `${hours}:${minutes}`; // Return time in HH:mm format
  } else {
    return ''; // Return empty string in case of invalid date
  }
}

limitHours(event: Date) {
  if (event) {
    this.hoursExceededError=false;
    const workedMinutes = this.convertTimeToMinutes(this.formatTimeToHHmm(event));
    const formData = this.timesheetEntryForm.value;
    const projectCode = formData.project_code;
    if(workedMinutes>480){
      this.hoursExceededError=true;
    }
  }
  else{
    const workedHoursControl = this.timesheetEntryForm.get('worked_hours');
    if (!workedHoursControl || !workedHoursControl.value) {
      // If no value, we set to 00:00 (Date object)
      const zeroTime = new Date();
      zeroTime.setHours(0, 0, 0, 0);
      workedHoursControl?.setValue(zeroTime);
      return; 
    }
  }
}

validateTime(event: any) {
  this.hoursExceededError=false;
  const workedHoursControl = this.timesheetEntryForm.get('worked_hours');
  if (workedHoursControl && workedHoursControl.value) {
    const workedMinutes = this.convertTimeToMinutes(this.formatTimeToHHmm(workedHoursControl.value));
    const formData = this.timesheetEntryForm.value;
    const projectCode = formData.project_code;
    if(workedMinutes>480){
      this.hoursExceededError=true;
    }
  }
  else{
    if (!workedHoursControl || !workedHoursControl.value) {
      // If no value, we set to 00:00 (Date object)
      const zeroTime = new Date();
      zeroTime.setHours(0, 0, 0, 0);
      workedHoursControl?.setValue(zeroTime);
      return; 
    }
  }
}

// Convert HH:mm time format to minutes
convertTimeToMinutes(time: string): number {
  if (!time) return 0;
  const [hours, minutes] = time.split(":").map(Number);
  return hours * 60 + minutes;
}

// Convert minutes to HH:mm format
convertMinutesToTime(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`;
}

// // only future date validation
// canClick(timesheetData: any): boolean {
//   const currentDate = new Date();

//   const [dd, mm, yyyy] = timesheetData.date.split('-');
//   const modifiedDate = `${yyyy}-${mm}-${dd}`;
//   const timesheetDate = new Date(modifiedDate);
  
//   console.log("currentDate:::", currentDate);
//   console.log("timesheetDate:::", timesheetDate);

//     // Reset both dates to midnight to ignore the time portion
//     currentDate.setHours(0, 0, 0, 0);
//     timesheetDate.setHours(0, 0, 0, 0);
  
//   // Format both dates as 'YYYY-MM-DD' in IST (Indian Standard Time)
//   //const formattedCurrentDate = currentDate.toLocaleDateString('en-IN', { timeZone: 'Asia/Kolkata' }).split('/').reverse().join('-'); // 'YYYY-MM-DD'
//   //const formattedTimesheetDate = timesheetDate.toLocaleDateString('en-IN', { timeZone: 'Asia/Kolkata' }).split('/').reverse().join('-'); // 'YYYY-MM-DD'

//   // if (timesheetData.status === 'approved' && timesheetData.worked_hours ) {
//   //   this.messageService.add({ severity: 'warn', summary: '', detail: 'Timesheet already approved for this date entry.' });
//   //   return false; // Prevent further actions if the status is 'approved'
//   // }

//   if (timesheetData.status !== 'approved' && timesheetDate > currentDate) {
//     this.messageService.add({ severity: 'warn', summary: 'Date validation', detail: 'Timesheets should not be added for future dates.' });
//     return false; // Prevent further actions
//   }

//   //return timesheetData.status !== 'approved' && formattedTimesheetDate <= formattedCurrentDate;
//   // return timesheetData.status !== 'approved' && timesheetDate <= currentDate;
//   return timesheetDate <= currentDate;
// }

//all validations with monday as start of week and sunday as end of week
canClick(timesheetData: any): boolean {
  const currentDate = new Date();
  // const currentDate = new Date('2025-12-01');

  // Parse dd-MM-yyyy format safely
  const [dd, mm, yyyy] = timesheetData.date.split('-');
  const timesheetDate = new Date(`${yyyy}-${mm}-${dd}`);
  timesheetDate.setHours(0, 0, 0, 0);
  currentDate.setHours(0, 0, 0, 0);

  // Allowed future limit = 7 days
  const maxAllowedDate = new Date(currentDate);
  maxAllowedDate.setDate(maxAllowedDate.getDate() + 7);

  // 1.Prevent future date entries ---
  // Restrict future beyond next 7 days
  if (timesheetDate > maxAllowedDate) {
  // if (timesheetDate > currentDate) {
    this.messageService.add({
      severity: 'warn',
      summary: 'Date validation',
      detail: 'You can enter timesheets only up to one week ahead from today.'
      // detail: 'You cannot enter timesheets for future dates.'
    });
    return false;
  }

  // 2.Calculate Monday of current week ---
  const currentDay = currentDate.getDay(); // Sunday=0, Monday=1, ...
  const daysSinceMonday = currentDay === 0 ? 6 : currentDay - 1;
  const weekStart = new Date(currentDate);
  weekStart.setDate(currentDate.getDate() - daysSinceMonday);
  weekStart.setHours(0, 0, 0, 0);

  // 3.Calculate next Monday ---
  const nextMonday = new Date(weekStart);
  nextMonday.setDate(weekStart.getDate() + 7);
  nextMonday.setHours(0, 0, 0, 0);

  // 4.Get month/year values ---
  const timesheetMonth = timesheetDate.getMonth();
  const timesheetYear = timesheetDate.getFullYear();
  const currentMonth = currentDate.getMonth();
  const currentYear = currentDate.getFullYear();

  // // Rejected entries editable within same month
  // if (timesheetData.status === 'rejected') {
  //   // Allow editing if it's from the same month and year
  //   if (timesheetMonth === currentMonth && timesheetYear === currentYear) {
  //     return true;
  //   }
  //   // If rejected but previous month, still prevent edits
  //   this.messageService.add({
  //     severity: 'warn',
  //     summary: 'Edit not allowed',
  //     detail: 'Rejected timesheets from previous months cannot be edited.'
  //   });
  //   return false;
  // }

  // // 5.Restrict to current week only for non-rejected entries ---
  // if (timesheetDate < weekStart) {
  //   this.messageService.add({
  //     severity: 'warn',
  //     summary: 'Week validation',
  //     detail: 'Timesheet entries must be submitted within the same week.'
  //   });
  //   return false;
  // }

  if(this.isTSAdmin === true) {
    return true; // Admins can edit any entry
  }

  // 6.Restrict previous month entries ---
  if (
    timesheetYear < currentYear ||
    (timesheetYear === currentYear && timesheetMonth < currentMonth)
  ) {
    const isSameWeek = timesheetDate >= weekStart && timesheetDate <= currentDate;
    if (!isSameWeek) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Month-end validation',
        detail: 'You cannot submit previous month entries after the new month has started.'
      });
      return false;
    }
  }

  return true; // Passed all checks
}

applyFilterGlobal($event:any, stringVal:any) {
  this.dt!.filterGlobal(($event.target as HTMLInputElement).value, stringVal);
}

}
