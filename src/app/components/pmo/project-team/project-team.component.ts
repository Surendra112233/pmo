import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, OnInit, Output, ViewChild } from '@angular/core';
import { FormGroup, FormControl, Validators, ReactiveFormsModule, FormBuilder,FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ConfirmationService, MessageService } from 'primeng/api';
import { CalendarModule } from 'primeng/calendar';
import { DropdownModule } from 'primeng/dropdown';
import { ToastModule } from 'primeng/toast';
import { Table, TableModule } from 'primeng/table';
import { IconFieldModule } from 'primeng/iconfield';
import { InputIconModule } from 'primeng/inputicon';
import { DialogModule } from 'primeng/dialog';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { CheckboxModule } from 'primeng/checkbox';
import { MasterDataService} from '../../../services/master-data.service';
import { ActivatedRouterService } from '../../../services/activated-router-service';
import { PMOService} from '../../../services/pmo.service';
import { ProjectTeam} from '../../../models/project-team';
import { NumbersOnlyDirective } from 'src/app/directives/numbers-only.directive';
import { DisableKeysDirective } from 'src/app/directives/disable-keys.directive';
import { catchError, forkJoin, of, tap } from 'rxjs';
import { AddAllocationPercentComponent } from '../add-allocation-percent/add-allocation-percent.component';
@Component({
  selector: 'app-project-team',
  imports: [ReactiveFormsModule, ToastModule, CalendarModule, CommonModule, DropdownModule,
    TableModule, CommonModule, InputIconModule, IconFieldModule, ToastModule, DialogModule,
            ConfirmDialogModule, CheckboxModule, FormsModule, ReactiveFormsModule, NumbersOnlyDirective,
          DisableKeysDirective, AddAllocationPercentComponent],
  templateUrl: './project-team.component.html',
  styleUrls: ['./project-team.component.scss'],
  providers: [ConfirmationService, MessageService],
  standalone:true
})
export class ProjectTeamComponent implements OnInit{
  @ViewChild('dt2') dt : Table | undefined
  @ViewChild('dt3') dt3 : Table | undefined
  // @Input() employeeDetails:any[]=[];
  @Input() projectCode:string='';
  @Input() projectsData:any;
  @Output() allocatedHoursChanged = new EventEmitter<number>(); 
  @Output() updateProjectAssignmentEvent = new EventEmitter(); 
  @Output() submitButtonHide = new EventEmitter<boolean>(); 
  projectTeam:any[]=[];
  projectRoles:any[]=[];
  displayDeleteDialog:boolean=false;
  selectedProjectRow:any;
  rowIndex:number=0;
  tasks:any[]=[];
  allEmpDetails:any[]=[];
  projectTeamModel:ProjectTeam[]=[];
  editRows: boolean[] = [];
  // minDate: string='';
  // maxDate:string='';
  // minEndDate:string='';
  // isStartDateValue:boolean=false;
  projectAllocatedHours:number = 0;
  totalprojectAllocatedHours:number=0;
  projectStartDate:any;
  projectEndDate:any;
  hasDuplicateError: boolean = false;
  dataLoaded: boolean = false;


  constructor(private masterDataService:MasterDataService,private activatedRouterService:ActivatedRouterService,
     private messageService:MessageService,private pmoService:PMOService,private router:Router){}
  
  ngOnInit(): void {
    this.getEmployeeDetails();
  }

  getEmployeeDetails() {
      this.masterDataService.getEmployeeDetails().subscribe(res=>{
      this.allEmpDetails = res['data'];
      this.allEmpDetails.sort((a, b) => a.employee_code.localeCompare(b.employee_code));
      this.allEmpDetails = this.allEmpDetails.map(emp => ({
        ...emp,
        formattedLabel: `${emp.employee_code} - ${emp.name}`  // Concatenating code & name
      }));


      this.getProjectRoles();
      // this.getTasks();
      this.getPhases();
      if(this.projectCode){
        this.getProjectTeam();
      }
    })
  }

  getProjectRoles(){
    this.masterDataService.getProjectRoles().subscribe(res=>{
      this.projectRoles=res['data'];
       this.projectRoles.sort((a, b) => a.project_role.localeCompare(b.project_role));
    });
  }

  getProjectTeam(){    
    this.projectTeam=[];
    this.pmoService.getProjectTeam(this.projectCode).subscribe(res=>{
      this.projectTeam=res;
      this.projectTeam = this.projectTeam.map(member => {
        return {
          ...member,
          start_date: new Date(member.start_date),
          end_date: new Date(member.end_date),
          joining_date: new Date(member.joining_date)
        };
      });
      this.projectAllocatedHours = this.projectsData?.allocated_budgeted_hours; 
      console.log("this.projectAllocatedHours:::", this.projectAllocatedHours);
      this.editRows = this.projectTeam.map(project => !project.id);
      this.projectStartDate = new Date(this.projectsData?.from_date);
      this.projectEndDate = new Date(this.projectsData?.to_date);
      this.dataLoaded = true; 
    }, (err)=> {
      this.dataLoaded = true;
      this.activatedRouterService.updateError(err, this.messageService);
    });
  }
  // getTasks(){
  //   this.masterDataService.getTasks().subscribe(res=>{
  //    this.tasks=res['data'];
  //   })
  // }

  getPhases() {
    this.pmoService.getPhasesByProject(this.projectCode).subscribe((res:any)=> {
      this.tasks=res;
      // this.tasks =this.tasks.map((task:any) => {
      //   if(task.phase_name == "Organization Standard Tasks"  && task.project_code == "RBXint0001") {
      //     return {
      //       ...task,
      //       task: 59 //changing 70 to 59
      //     }
      //   } else {
      //     return {
      //       ...task
      //     }
      //   }
      // })
      // console.log("this.tasks:::", this.tasks);
    })
  }

  addProjectTeam() {
    const newRow = {
      // uiId: `temp_${Date.now()}_${Math.floor(Math.random() * 1000)}`, // only for UI
      project_code: '',
      employee_code: '',
      employee_name: '',
      designation: '',
      project_role: '',
      start_date: '',
      end_date: '',
      task: '',
      allocated_hours: '',
      isEdit: false,
    };

    // Push new row at the END
    this.projectTeam = [...this.projectTeam, newRow];
    // this.selectedProjectTeam = []; // clear selection to avoid default check
    
    // Hide submit button until user finishes editing
    this.submitButtonHide.emit(true);

    // Jump to last page to show new row
    setTimeout(() => {
      const totalRecords = this.projectTeam.length;
      const rowsPerPage = 10; // since you set [rows]="10" in HTML
      const lastPage = Math.ceil(totalRecords / rowsPerPage) - 1;

      if (this.dt) {
        this.dt.first = lastPage * rowsPerPage; // move paginator
      }
    });
  }  

  isSubmitDisabled(): boolean {
    return this.projectTeam.some(team => 
      !team.employee_code || 
      !team.employee_name || 
      !team.designation || 
      !team.project_role || 
      !team.start_date || 
      !team.end_date || 
      !team.task || 
      // !team.allocated_hours ||
      team.allocated_hours === null || team.allocated_hours === undefined || team.allocated_hours === '' ||
      team.hasDuplicate
    );
  }

  navigateToGrid() {
    this.router.navigate(['/pmo/project-assignment']);
  }

  changeFormat(dateToTransfer:string){
    const date = new Date(dateToTransfer);
    const formattedDate = date.getFullYear() + '-' +
      String(date.getMonth() + 1).padStart(2, '0') + '-' +
      String(date.getDate()).padStart(2, '0');
    return formattedDate
  }

  displayChangedFormat(dateToTransfer:string){
    const date = new Date(dateToTransfer);
    const formattedDate =       
      String(date.getDate()).padStart(2, '0') + '-' +
      String(date.getMonth() + 1).padStart(2, '0') + '-' +
      date.getFullYear();

    return formattedDate
  }

  onSubmitProjectTeam() {
  
    if (this.totalprojectAllocatedHours > this.projectAllocatedHours) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Warning',
        detail: 'Total allocated hours exceed project limit.',
      });
      return; // Stop further execution if the limit is exceeded
    }

    console.log(this.projectTeam);
    this.projectTeam = this.projectTeam.map(element => ({
      ...element,
      project_code: this.projectCode,
      task: +element.task,
      project_role: +element.project_role,
      start_date: this.changeFormat(element.start_date),
      end_date: this.changeFormat(element.end_date)
    }));
  
    const newRecords = this.projectTeam.filter(element => !element.id);
    const existingRecords = this.projectTeam.filter(element => element.id && element.isEdit==true);
    let count=0;
    if (newRecords.length > 0) {
      console.log("newRecords::", newRecords);
      this.pmoService.addProjectTeam(newRecords).subscribe(
            data=>{
              this.getProjectTeam();
              this.updateProjectAssignmentEvent.emit();
              count=count+1;
            this.messageService.add({ severity: 'success', summary: '', detail: 'Project Team Created Successfully' });
            setTimeout(() => {
            }, 1000);
          },(err: any) => {
            console.log(err, err?.error?.error);
            const errMsg = err?.error?.errors?.[0]?.error || err?.error?.[0]?.non_field_errors?.[0] || err?.error?.error  || err?.error?.errors?.[0]?.error;
            this.messageService.add({ severity: 'error', summary: '', detail: errMsg });
            setTimeout(() => {
              const currentRoute = this.router.url;
              this.router.navigateByUrl('/', { skipLocationChange: true }).then(() => {
                this.router.navigateByUrl(currentRoute);
              });
            }, 3000) 
          });
    }
    if (existingRecords.length > 0) {
      // Remove 'isEdit' and 'id' properties
      const payload = existingRecords.map(({isEdit, ...rest }) => rest);
      this.pmoService.updateProjectTeam(payload,this.projectCode).subscribe(
        data=>{
          this.getProjectTeam();
            if(count==0)
            {
            this.updateProjectAssignmentEvent.emit();
            }
        this.messageService.add({ severity: 'success', summary: '', detail: 'Project Team Update Successfully' });
        setTimeout(() => {
        }, 1000);
      },(err: any) => {
        console.log(err); 
        // this.activatedRouterService.updateError(err, this.messageService);
        const errMsg = err?.error?.error || err?.error?.errors?.[0]?.non_field_errors?.[0] || err?.error?.errors?.non_field_errors || err?.error?.errors?.[0]?.error
        this.messageService.add({ severity: 'error', summary: '', detail: errMsg });
        setTimeout(() => {
          const currentRoute = this.router.url;
          this.router.navigateByUrl('/', { skipLocationChange: true }).then(() => {
            this.router.navigateByUrl(currentRoute);
          });
        }, 3000)
      });
    }
  this.submitButtonHide.emit(false);    
  }

  onChangeEmployee(employee_code: string, rowIndex: number) {
    // this.hasDuplicateError = false;

    const selectedEmployeeData = this.allEmpDetails.find((employee: any) => employee.employee_code === employee_code);
    if (selectedEmployeeData) {
      this.projectTeam[rowIndex].employee_name = selectedEmployeeData.name;
      this.projectTeam[rowIndex].designation = selectedEmployeeData.designation;
      this.projectTeam[rowIndex].joining_date = new Date(selectedEmployeeData.joining_date);
    }

    // const selectedPhase = this.projectTeam[rowIndex].task;
    // // Check if the employee is already added with the same phase
    // const duplicateEntry = this.projectTeam.some((item, index) =>
    //   index !== rowIndex && item.employee_code === employee_code && item.task === Number(selectedPhase)
    // );

    // if (duplicateEntry) {
    //   this.hasDuplicateError = true;
    //   this.messageService.add({ severity: 'error', summary: '', detail: 'This employee is already assigned with the selected phase.' });
    //   // this.projectTeam.splice(rowIndex, 1);
    //   return;
    // }
    this.checkForDuplicates();

    // // const countOfEmployeeCode = this.projectTeam.filter(item => item.employee_code === employee_code).length;
    // // const employeeCodeExists = this.projectTeam?.some(item => item.employee_code === employee_code);
    // // if (countOfEmployeeCode > 1) {
    // //   this.messageService.add({ severity: 'error', summary: '', detail: 'This employee has already been added to the project team.' });
    // //   this.projectTeam.splice(rowIndex, 1);
    // //   return;
    // // }
  }

  showDeleteDialog(project:any,rowIndex:number){
    this.displayDeleteDialog = true;
    this.selectedProjectRow=project;
    this.rowIndex=rowIndex;
  }

  closeDeleteDialog() {
    this.displayDeleteDialog = false;
    this.selectedProjectRow=null;
    this.rowIndex=0;
  }

deleteProjectTeam() {
  // this.updateProjectAllocatedHours(this.selectedProjectRow.allocated_hours);

  const isServerRecord = this.selectedProjectRow?.id;
  const indexToDelete = this.rowIndex;

  const removeFromList = () => {
    if (indexToDelete >= 0 && indexToDelete < this.projectTeam.length) {
      this.projectTeam.splice(indexToDelete, 1);
      this.projectTeam = [...this.projectTeam]; // trigger UI update

      // Adjust paginator
      setTimeout(() => {
        if (this.dt) {
          const totalRecords = this.projectTeam.length;
          const rowsPerPage = this.dt.rows || 10;
          const currentPage = Math.floor(this.dt.first! / rowsPerPage);
          const lastPage = Math.floor((totalRecords - 1) / rowsPerPage);
          
          if (currentPage > lastPage) {
            this.dt.first = lastPage * rowsPerPage;
          }
        }
      });
    }
  };

  if (isServerRecord) {
    this.pmoService.deleteProjectTeam(this.selectedProjectRow.id).subscribe(
      data => {
        this.messageService.add({ severity: 'success', summary: '', detail: 'Deleted Successfully' });
        removeFromList();
        setTimeout(() => {
          this.updateProjectAssignmentEvent.emit();
        }, 500);
      },
      err => {
        this.activatedRouterService.updateError(err, this.messageService);
      }
    );
  } else {
    removeFromList();
  }

  this.displayDeleteDialog = false;
}

  applyFilterGlobal($event:any, stringVal:any) {
    this.dt!.filterGlobal(($event.target as HTMLInputElement).value, stringVal);
  }

  applyAllocationFilterGlobal($event:any, stringVal:any) {
    this.dt3!.filterGlobal(($event.target as HTMLInputElement).value, stringVal);
  }

  edit(project: any) {
    project.isEdit = true;
    this.submitButtonHide.emit(true);
  }

  testEnddate(end_date:any,start_date:any, record:any) {
    const projectStart = new Date(this.projectStartDate);
    const new_start_date = new Date(this.changeFormat(start_date));
    const new_end_date = new Date(this.changeFormat(end_date));

     // Find the actual record in projectTeam
    const index = this.projectTeam.findIndex(p =>
      p.employee_code === record.employee_code &&
      p.task === record.task &&
      p.id === record.id
    );

    if (index === -1) return; // safety check

    // End date must be >= start date
    if (start_date && end_date && new_start_date > new_end_date) {
      this.messageService.add({
        severity: 'error',
        summary: 'Date Validation Error',
        detail: 'End date must be greater than or equal to start date.'
      });
      this.projectTeam[index].end_date = null;
      // record.end_date = null;
      return;
    }

    // Start date must be >= project start
    if (start_date && new_start_date < projectStart) {
      this.messageService.add({
        severity: 'error',
        summary: 'Date Validation Error',
        detail: 'Start date must be greater than or equal to project start date.'
      });
      this.projectTeam[index].start_date = null;
      // record.start_date = null;
      return;
    }

    // End date must be >= project start
    if (end_date && new_end_date < projectStart) {
      this.messageService.add({
        severity: 'error',
        summary: 'Date Validation Error',
        detail: 'End date must be greater than or equal to project start date.'
      });
      this.projectTeam[index].end_date = null;
      // record.end_date = null;
      return;
    }
  }

  onPhaseChange(project: any, rowIndex: number) {
    const selectedPhaseId = this.projectTeam[rowIndex].task;
    const selectedEmpCode = this.projectTeam[rowIndex].employee_code;

    //1. Check for duplicates (keep your existing logic)
    this.checkForDuplicates();
    // const duplicateEntry = this.projectTeam.some((item, index) =>
    //   index !== rowIndex &&
    //   item.employee_code === selectedEmpCode &&
    //   Number(item.task) === Number(selectedPhaseId)
    // );

    // if (duplicateEntry) {
    //   this.messageService.add({
    //     severity: 'error',
    //     summary: '',
    //     detail: 'This employee is already assigned with the selected phase.'
    //   });
    //   this.projectTeam[rowIndex].hasDuplicate = true;
    //   this.hasDuplicateError = true;
    //   return;
    // } else {
    //   this.projectTeam[rowIndex].hasDuplicate = false;
    //   this.hasDuplicateError = false;
    // }

    //2. Update min/max dates for the selected phase
    const selectedPhase = this.tasks.find(t => Number(t.task) === Number(selectedPhaseId));
    if (selectedPhase) {
      project.phase_start_date = new Date(selectedPhase.start_date);
      project.phase_end_date = new Date(selectedPhase.end_date);

      // If current dates fall outside range, adjust/reset them
      const start = new Date(project.start_date);
      const end = new Date(project.end_date);

      if (isNaN(start.getTime()) || start < project.phase_start_date) {
        project.start_date = project.phase_start_date;
      }
      if (isNaN(end.getTime()) || end > project.phase_end_date) {
        project.end_date = project.phase_end_date;
      }
    } else {
      // Reset phase date limits if no phase found
      project.phase_start_date = null;
      project.phase_end_date = null;
    }

    // Optionally re-check duplicates globally
    // this.checkForDuplicates();
  }

  checkForDuplicates() {
    let duplicateExists = false;

    this.projectTeam.forEach((current, index) => {
      current.hasDuplicate = false; // reset before checking
      if (!current.employee_code || !current.task) return;

      const isDuplicate = this.projectTeam.some((other, otherIndex) =>
        otherIndex !== index &&
        other.employee_code === current.employee_code &&
        Number(other.task) === Number(current.task)
      );

      current.hasDuplicate = isDuplicate;
      if (isDuplicate) duplicateExists = true;      
    });
    
    this.hasDuplicateError = duplicateExists;

      if (duplicateExists) {
        this.messageService.add({
          severity: 'error',
          summary: '',
          detail: 'This employee is already assigned with the selected phase.'
        });
      }
  }
}
