
import { CommonModule } from '@angular/common';
import { Component, OnInit, signal } from '@angular/core';
import { FormBuilder, FormControl, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ConfirmationService, MessageService } from 'primeng/api';
import { CalendarModule } from 'primeng/calendar';
import { DropdownModule } from 'primeng/dropdown';
import { ToastModule } from 'primeng/toast';
// import * as moment from 'moment-timezone';
// import 'moment-timezone';
import { LoginService } from '../../../../services/login.service';
import { ActivatedRouterService } from '../../../../services/activated-router-service';
import { MasterDataService} from '../../../../services/master-data.service';
import { Tasks} from '../../../../models/tasks';
import { NoSpaceDirective } from 'src/app/directives/no-space.directive';
import { AlphaNumericSpecialCharsDirective } from 'src/app/directives/alphanumeric.directive';
import { FirstLetterCapitalDirective } from 'src/app/directives/first-letter-capital.directive';

@Component({
    selector: 'app-add-project-roles',
    imports: [ReactiveFormsModule, ToastModule, CalendarModule, CommonModule, DropdownModule,FirstLetterCapitalDirective,NoSpaceDirective,
      AlphaNumericSpecialCharsDirective
    ],
    templateUrl: './add-project-roles.component.html',
    styleUrls: ['./add-project-roles.component.scss'],
    providers: [ConfirmationService, MessageService],
    standalone:true
})
export class AddProjectRolesComponent implements OnInit{
  projectRolesForm!: FormGroup;
  projectTypeList:any=[];
  taskGroupList:any=[];
  billableList:any=[];
  projectRoles:any; 
  projectRoleId:string='';
  buttonValue:string='Submit';
  taskHeaderText='Add Project Roles';
  constructor(
    private loginService:LoginService,
    private formBuilder: FormBuilder,
    private router: Router,
    private messageService: MessageService,private activatedRoute:ActivatedRoute,
     private activatedRouterService: ActivatedRouterService,private masterDataService:MasterDataService
  ) {}
  ngOnInit(): void {
      this.projectRolesForm = this.formBuilder.group({
        project_role: new FormControl('', [Validators.required,Validators.minLength(3), Validators.maxLength(100)])       
      });
      this.activatedRoute.paramMap.subscribe(params => {
        this.projectRoleId = params.get('id') || '';
        if(this.projectRoleId){
          this.getProjectRolesById();
          this.buttonValue='Update';
          this.taskHeaderText='Edit Project Roles';
        }
        else{
         this.buttonValue='Submit';
         this.taskHeaderText='Add Project Roles';
        }
      });
     
  }

  getFormControl(formControlName:string) {
    return this.projectRolesForm.get(formControlName);
  }

  getProjectRolesById(){
    this.masterDataService.getProjectRolesById(+this.projectRoleId).subscribe(res=>{
      this.projectRoles=res['project_role'];
   //  const projectRoles=this.projectRoles.find(r=>r.id==+this.projectRoleId);
      this.projectRolesForm.patchValue({
        project_role:this.projectRoles?.project_role,
        id: this.projectRoles?.id,      
      })
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  onSubmit(){ 
    if(this.projectRoleId){
      var projectRoles={
        "project_role": this.projectRolesForm.get('project_role')?.value,
        "id": +this.projectRoleId
      } 
      this.masterDataService.updateProjectRoles(+this.projectRoleId,projectRoles).subscribe(res=>{
        this.messageService.add({ severity: 'success', summary: '', detail: 'Project Role Updated Successfully' });
        setTimeout(() => {
          this.navigateToGrid()
        }, 1000);
      },(err: any) => { 
        this.activatedRouterService.updateError(err, this.messageService)
      })
    }
else{
    this.masterDataService.addProjectRoles(this.projectRolesForm.value).subscribe(res=>{
      this.messageService.add({ severity: 'success', summary: '', detail: 'Project Role added successfully' });
      setTimeout(() => {
        this.navigateToGrid()
      }, 1000);
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }
  }

  navigateToGrid(){
    this.router.navigate(['/md/project_roles']);
  }

  back(){
   this.projectRoleId ? this.router.navigate(['/md/view_project_roles'],{ queryParams: { id: this.projectRoleId} }):this.router.navigate(['/md/project_roles']);
  }
}

