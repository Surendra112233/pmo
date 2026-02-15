import { CommonModule } from '@angular/common';
import { Component, OnInit, ViewChild } from '@angular/core';
import { Table, TableModule } from 'primeng/table';
import { IconFieldModule } from 'primeng/iconfield';
import { InputIconModule } from 'primeng/inputicon';
import { Router } from '@angular/router';
import { ConfirmationService, MessageService } from 'primeng/api'
import { ToastModule } from 'primeng/toast';
import { DialogModule } from 'primeng/dialog';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { CheckboxModule } from 'primeng/checkbox';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRouterService } from '../../../services/activated-router-service';
import { MasterDataService} from '../../../services/master-data.service';
import { Tasks } from '../../../models/tasks';

@Component({
    selector: 'app-project-roles',
    imports: [TableModule, CommonModule, InputIconModule, IconFieldModule, ToastModule, DialogModule,
        ConfirmDialogModule, CheckboxModule, FormsModule, ReactiveFormsModule],
    templateUrl: './project-roles.component.html',
    styleUrls: ['./project-roles.component.scss'],
    providers: [ConfirmationService, MessageService],
    standalone:true
})
export class ProjectRolesComponent implements OnInit{
  @ViewChild('dt2') dt : Table | undefined
projectRoles:any[]=[];
constructor(private router:Router,private masterDataService:MasterDataService,
  private activatedRouterService:ActivatedRouterService,private messageService:MessageService){}

  ngOnInit(): void {
    this.getProjectRoles();
    
  }

  getProjectRoles(){
  this.masterDataService.getProjectRoles().subscribe(res=>{
    this.projectRoles=res['data'];
    this.projectRoles.sort((a, b) => b.id - a.id);
  },(err: any) => { 
    this.activatedRouterService.updateError(err, this.messageService)
  })
  }

  applyFilterGlobal($event:any, stringVal:any) {
    this.dt!.filterGlobal(($event.target as HTMLInputElement).value, stringVal);
  }
  navigateToGrid(){
    this.router.navigate(['/md/project_tasks']);
  }

  navigateToView(task_code:number){
    this.router.navigate(['/md/view_project_roles'], { queryParams: { id: task_code} });    
  }

  addProjectRoles(){
    this.router.navigate(['/md/add_project_roles']);
  }
  editTask(task_code:number){
    this.router.navigate(['/md/edit_task',task_code]);
  }
  
}

