import { Component, OnInit, ViewChild } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ToastModule } from 'primeng/toast';
import { FormBuilder, FormControl, FormGroup, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { CalendarModule } from 'primeng/calendar';
import { CheckboxModule } from 'primeng/checkbox';
import { RadioButtonModule } from 'primeng/radiobutton';
import { UserService } from '../../../services/user.service';
import { MessageService } from 'primeng/api';
import { ActivatedRouterService } from '../../../services/activated-router-service';
import { PMOService} from '../../../services/pmo.service';
import { pmo } from '../../../models/pmo';
import { Table, TableModule } from 'primeng/table';
import { DialogModule } from 'primeng/dialog';
@Component({
    selector: 'app-view-project-assignment',
    imports: [ToastModule, CommonModule, ReactiveFormsModule, CalendarModule, 
      FormsModule, CheckboxModule, RadioButtonModule, TableModule, DialogModule],
    templateUrl: './view-project-assignment.component.html',
    styleUrls: ['./view-project-assignment.component.scss'],
    providers: [MessageService],
    standalone:true
})
export class ViewProjectAssignmentComponent implements OnInit{
  @ViewChild('dt') dt : Table | undefined
  @ViewChild('dt3') dt3 : Table | undefined
  project_code:string='';
 // projectForm!: FormGroup;
 phaseAllocations: any[] = [];
  projects:pmo=new pmo();
  projectTeam: any[] = [];

  constructor(
    private router:Router,
    private formBuilder:FormBuilder,
    private activatedRoute:ActivatedRoute,
    private userService:UserService,private messageService: MessageService,
        private activatedRouterService: ActivatedRouterService,private pmoService:PMOService
  ) {}

  ngOnInit(): void {
    this.activatedRoute.queryParams.subscribe((res) => {
      this.project_code=res['id']
    });
    this.getProjectsById();
  }

  getProjectsById(){
    this.pmoService.getProjectsById(this.project_code).subscribe(res=>{
     this.projects=res['data'];
     this.getPhaseWiseAllocation();
     this.getProjectTeam();
   },(err: any) => { 
     this.activatedRouterService.updateError(err, this.messageService)
   })
 }

  navigateToGrid() {
    this.router.navigate(['/pmo/project-assignment']);
  }

  navigateToEditProject() {
    this.router.navigate(['/pmo/edit-project-assignment',this.project_code]);
  }

  changeFormat(dateToTransfer:string){
    const date = new Date(dateToTransfer);
    const formattedDate = date.getFullYear() + '-' +
      String(date.getMonth() + 1).padStart(2, '0') + '-' +
      String(date.getDate()).padStart(2, '0');
    return formattedDate
  }

  getPhaseWiseAllocation() {
    this.pmoService.getPhasesByProject(this.project_code).subscribe((res:any)=>{
      this.phaseAllocations = res || [];
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    });
  }

  //convert HH:MM into a cleaner format
  formatWorkedHours(worked: string): string {
    if (!worked || worked === "00:00") return "0:00";
    return worked;
  }

  getProjectTeam() {
    this.pmoService.getProjectTeam(this.project_code).subscribe(res=>{
      this.projectTeam = res || [];
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    });
  }

  applyFilterGlobal($event:any, stringVal:any) {
    this.dt!.filterGlobal(($event.target as HTMLInputElement).value, stringVal);
  }
}
