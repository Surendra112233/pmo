import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ToastModule } from 'primeng/toast';
import { FormBuilder, FormControl, FormGroup, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { CalendarModule } from 'primeng/calendar';
import { CheckboxModule } from 'primeng/checkbox';
import { RadioButtonModule } from 'primeng/radiobutton';
import { MasterDataService } from '../../../../services/master-data.service';
import { MessageService } from 'primeng/api';
import { ActivatedRouterService } from '../../../../services/activated-router-service';

@Component({
    selector: 'app-view-project-roles',
    imports: [ToastModule, CommonModule, ReactiveFormsModule, CalendarModule, FormsModule, CheckboxModule, RadioButtonModule],
    templateUrl: './view-project-roles.component.html',
    styleUrls: ['./view-project-roles.component.scss'],
    providers: [MessageService],
    standalone:true
})
export class ViewProjectRolesComponent implements OnInit{
  projectRoleId:string='';
//  projectRolesForm!: FormGroup;
  projectRoles:any;
  constructor(
    private router:Router,
    private formBuilder:FormBuilder,
    private activatedRoute:ActivatedRoute,
    private masterDataService:MasterDataService,private messageService: MessageService,
        private activatedRouterService: ActivatedRouterService
  ) {}

  ngOnInit(){
    // this.projectRolesForm = this.formBuilder.group({
    //  id: new FormControl(''),
    //   project_role: new FormControl(''),    
    // })
    this.activatedRoute.queryParams.subscribe((res) => {
      this.projectRoleId=res['id'];
      this.getProjectRolesById();
    })
  }

  getProjectRolesById(){
    this.masterDataService.getProjectRolesById(Number(this.projectRoleId)).subscribe(res=>{
      this.projectRoles=res['project_role']; 

      // this.projectRolesForm.patchValue({
      //   project_role:this.projectRoles?.project_role,
      //   id: this.projectRoles?.id,      
      // })
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  navigateToGrid() {
    this.router.navigate(['/md/project_roles'],{ queryParams: { id: this.projectRoleId}});
  }

  navigateToEditProjectRole() {    
    this.router.navigate(['/md/edit_project_roles',this.projectRoleId]);
  }

}
