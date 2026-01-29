import { Component, EventEmitter, Input, Output, ViewChild} from '@angular/core';
import { ToastModule } from 'primeng/toast';
import { ActivatedRouterService } from 'src/app/services/activated-router-service';
import { MessageService } from 'primeng/api';
import { DropdownModule } from 'primeng/dropdown';
import { FormBuilder, FormControl, FormGroup, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { MasterDataService } from 'src/app/services/master-data.service';
import { Router } from '@angular/router';
import { Table, TableModule } from 'primeng/table';
import { PMOService } from 'src/app/services/pmo.service';
import { CalendarModule } from 'primeng/calendar';
import { DialogModule } from 'primeng/dialog';
import { DisableKeysDirective } from 'src/app/directives/disable-keys.directive';
import { timer } from 'rxjs';

@Component({
  standalone: true,
  selector: 'app-add-allocation-percent',
  templateUrl: './add-allocation-percent.component.html',
  styleUrls: ['./add-allocation-percent.component.scss'],
  imports: [ToastModule, DropdownModule, ReactiveFormsModule, CalendarModule, DialogModule,
      CommonModule, FormsModule, TableModule, DisableKeysDirective],
})
export class AddAllocationPercentComponent {
  @Input() from_projectTeam:boolean = false;
  @Output() close_dialog = new EventEmitter<boolean>();
  @ViewChild('dt2') dt2 : Table | undefined;
  @ViewChild('dt3') dt3 : Table | undefined;

  employeesList: any[] = [];
  empProjectDetails: any = [];
  currentUser: string = '';
  allocationPercentForm!: FormGroup;
  isEmpLoading:boolean = true;
  showHistoryDialog = false;
  selectedHistory: any[] = [];
  latestTimestamp:any;

  showOverlapDialog: boolean = false;
  overlapList: any[] = [];
  selectedEmployeeCode: string = "";

  timer$ = timer(1000);


  constructor(
    private masterDataService: MasterDataService,
    private pmoService: PMOService,
    private activatedRouterService: ActivatedRouterService,
    private messageService: MessageService,
    private fb: FormBuilder,
    private router: Router
  ){}
 
  ngOnInit() {
    this.getEmployees();

    this.allocationPercentForm = new FormGroup({
      employee_code : new FormControl('')
    })

    this.currentUser = localStorage.getItem('user_name') || '';
  }

  getEmployees(){
    this.isEmpLoading = true;
    this.masterDataService.getEmployeeDetails().subscribe(res=>{
      this.employeesList=res['data'].map((emp: { employee_code: any; name: any; }) => ({
        ...emp,
        employee_codewithName: `${emp.employee_code} - ${emp.name}`
      }));
      this.employeesList = this.employeesList.sort((a:any,b:any) => a.employee_code.localeCompare(b.employee_code))
      this.isEmpLoading = false;
    },(err: any) => {
      this.isEmpLoading = false; 
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  getEmpProjectDetails(event:any){
    const emp_code = event.value;
    this.getAllocationDetails(emp_code);
  }

  getAllocationDetails(emp_code:string){
    this.pmoService.getEmpProjectDetails(emp_code).subscribe((res:any)=>{
    if(res) {
      // console.log(res);
      this.empProjectDetails = res
      .filter((proj: any) => proj.projectCode !== 'RB001')
      .map((proj:any) => ({
        projectCode: proj.projectCode,
        projectName: proj.projectName,
        managerName: proj.managerName,
        phases: proj.phases?.map((ph:any) => ({
          taskCode: ph.taskCode,
          phaseName: ph.phaseName,
          phaseStartDate: new Date(ph.phaseStartDate),
          phaseEndDate: new Date(ph.phaseEndDate),
          allocationPercent: ph.allocationPercent,
          allocationStartDate: ph.allocationStartDate ? new Date(ph.allocationStartDate) : null,
          allocationEndDate: ph.allocationEndDate ? new Date(ph.allocationEndDate) : null,
          allocationHistory: ph.allocationHistory ?? []
        }))              
      }));
    }
    }, (err:any) => {
        this.activatedRouterService.updateError(err, this.messageService);
    })
  }

  applyAllocationFilterGlobal($event:any, stringVal:any) {
    this.dt2!.filterGlobal(($event.target as HTMLInputElement).value, stringVal);
  }
  
  applyOverlapFilterGlobal($event:any, stringVal:any) {
    this.dt3!.filterGlobal(($event.target as HTMLInputElement).value, stringVal);
  }

  isAllocationValid(): boolean {
    if (!this.empProjectDetails || this.empProjectDetails.length === 0) {
      return false;
    }

    return this.empProjectDetails.every((project: any) => {

      // Project must contain at least one phase
      if (!project.phases || project.phases.length === 0) {
        return false;
      }

      return project.phases.every((phase: any) => {
        const percentValid =
          phase.allocationPercent !== null &&
          phase.allocationPercent !== undefined &&
          phase.allocationPercent !== '' &&
          phase.allocationPercent >= 0 &&
          phase.allocationPercent <= 100;

        const startValid =
          phase.allocationStartDate !== null &&
          phase.allocationStartDate !== undefined &&
          phase.allocationStartDate !== '';

        const endValid =
          phase.allocationEndDate !== null &&
          phase.allocationEndDate !== undefined &&
          phase.allocationEndDate !== '';

        return percentValid && startValid && endValid;
      });
    });
  }

  testEnddate(end_date:any, start_date:any, row:any) {
    const new_start_date = new Date(this.changeFormat(start_date));
    const new_end_date = new Date(this.changeFormat(end_date));

    // End date must be >= start date
    if (start_date && end_date && new_start_date > new_end_date) {
      this.messageService.add({
        severity: 'error',
        summary: 'Date Validation Error',
        detail: 'End date must be greater than or equal to start date.'
      });
      row.allocationEndDate = null;
      return;
    }
  }

  displayChangedFormat(dateToTransfer:string){
    const date = new Date(dateToTransfer);
    const formattedDate =       
      String(date.getDate()).padStart(2, '0') + '-' +
      String(date.getMonth() + 1).padStart(2, '0') + '-' +
      date.getFullYear();

    return formattedDate
  }

  changeFormat(dateToTransfer:string){
    const date = new Date(dateToTransfer);
    const formattedDate = date.getFullYear() + '-' +
      String(date.getMonth() + 1).padStart(2, '0') + '-' +
      String(date.getDate()).padStart(2, '0');
    return formattedDate
  }

  viewHistory(row: any) {
    this.selectedHistory = (row.allocationHistory || []).map((h: any) => ({
      ...h,
      fromDate: new Date(h.fromDate),
      toDate: new Date(h.toDate),
      timestamp: new Date(h.timestamp)
    }));

    // find the latest record by timestamp
    if (this.selectedHistory.length > 0) {
      const latest = this.selectedHistory.reduce((a: any, b: any) =>
        a.timestamp > b.timestamp ? a : b
      );
      this.latestTimestamp = latest.timestamp;
    } else {
      this.latestTimestamp = null;
    }

    this.showHistoryDialog = true;
  }

  onCancel() {
    if(this.from_projectTeam) {
      this.close_dialog.emit(false);
    } else {
      this.router.navigate(['/pmo/project-assignment']);
    }
  }

  onSubmit() {
    this.selectedEmployeeCode = this.allocationPercentForm.get('employee_code')?.value;

    // const payload = this.empProjectDetails.map((project: any) => ({
    //   projectCode: project.projectCode,
    //   allocationPercent: project.allocationPercent,
    //   allocationStartDate: this.changeFormat(project.allocationStartDate),
    //   allocationEndDate: this.changeFormat(project.allocationEndDate)
    // }));

    const payload:any[] = [];

    this.empProjectDetails.forEach((proj:any) => {
      proj.phases.forEach((ph:any) => {
        payload.push({
          projectCode: proj.projectCode,
          taskCode: ph.taskCode,
          // phaseName: ph.phaseName,
          allocationStartDate: this.changeFormat(ph.allocationStartDate),
          allocationEndDate: this.changeFormat(ph.allocationEndDate),
          allocationPercent: ph.allocationPercent
        });
      });
    });

    // console.log('Payload to save:', payload);
    this.saveAllocation(this.selectedEmployeeCode, payload);
  }

  saveOverlapFix() {
    const finalPayload = this.mergeUpdatedOverlapWithMainList();
    // console.log('Payload from dialog to save:', finalPayload);
    this.saveAllocation(this.selectedEmployeeCode, finalPayload);
  }

  mergeUpdatedOverlapWithMainList() {
    const mergedList: any[] = [];
    this.empProjectDetails.forEach((proj: any) => {
      proj.phases.forEach((phase: any) => {

        // Check if this phase exists in overlapList
        const updated = this.overlapList.find((record: any) => {
          return record.projectCode === proj.projectCode &&
                 Number(record.taskCode) === Number(phase.taskCode);
        });

        const item = updated
          ? {
              projectCode: updated.projectCode,
              taskCode: updated.taskCode,
              allocationPercent: updated.allocation_percent,
              allocationStartDate: this.changeFormat(updated.allocation_start_date),
              allocationEndDate: this.changeFormat(updated.allocation_end_date)
            }
          : {
              projectCode: proj.projectCode,
              taskCode: phase.taskCode,
              allocationPercent: phase.allocationPercent,
              allocationStartDate: this.changeFormat(phase.allocationStartDate),
              allocationEndDate: this.changeFormat(phase.allocationEndDate)
            };
        mergedList.push(item);
      });
    });

    return mergedList;
  }

  cancelOverlap() {
    this.showOverlapDialog = false;
  }

  removeHighlight(row: any): void {
    if (row.highlightAllocation) {
      row.highlightAllocation = false;
    }
  }

  saveAllocation(emp_code:string, payload:any) {
    this.pmoService.assignAllocationPercent(emp_code, payload).subscribe( data => {
      this.messageService.add({ severity: 'success', summary: '', detail: 'Allocation updated successfully' });
      this.showOverlapDialog = false;
      // setTimeout(() => {
      //   const currentRoute = this.router.url;
      //   this.router.navigateByUrl('/', { skipLocationChange: true }).then(() => {
      //     this.router.navigateByUrl(currentRoute);
      //   });
      // }, 3000);
      this.timer$.subscribe(() => {
        this.getAllocationDetails(emp_code);
      });
    
    },(err: any) => {
      if (err.error?.error === "Allocation exceeds 100% within overlapping date range") {

        this.overlapList = err.error.details.map((item: any) => ({
          ...item,
          phase_start_date: new Date(item.phase_start_date),
          phase_end_date: new Date(item.phase_end_date),
          allocation_start_date: new Date(item.allocation_start_date),
          allocation_end_date: new Date(item.allocation_end_date)
        }));

        this.overlapList = this.overlapList.map((item:any) => {
          return {
            ...item,
            highlightAllocation: true
          }      
        });

        this.showOverlapDialog = true;
        this.timer$.subscribe(() => {
          this.messageService.add({ severity: 'error', summary: 'Overlapping Found', detail: err.error?.error });
          // this.messageService.add({ severity: 'warn', summary: 'Overlapping Found', detail: 'Please adjust values again' });
        });
      } else {
        this.activatedRouterService.updateError(err, this.messageService);
      }
    });
  }
}