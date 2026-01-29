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
import { UserService } from '../../../services/user.service';
import { ActivatedRouterService } from '../../../services/activated-router-service';
import { User,User_Roles } from '../../../models/user';

@Component({
    selector: 'app-maintain-role',
    standalone:true,
    imports: [TableModule, CommonModule, InputIconModule, IconFieldModule, ToastModule, DialogModule,
      ConfirmDialogModule],
    templateUrl: './maintain-role.component.html',
    styleUrls: ['./maintain-role.component.scss'],
    providers: [ConfirmationService, MessageService]
})
export class MaintainRoleComponent {
  @ViewChild('dt2') dt : Table | undefined
  
  roles:any[] = [];

  constructor(
    private userService:UserService,
    private router:Router,    
    private messageService: MessageService,
    private activatedRouterService: ActivatedRouterService
  ) {}

  ngOnInit(){
    this.getAssignRoles()
  }

  getAssignRoles(){
  this.userService.getAssignRoles().subscribe((res) => {
       this.roles = res['users'].filter((user:any) => user.status.toLowerCase() == 'active');
       this.roles.sort((a, b) => b.id - a.id);
       console.log(this.roles);
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  applyFilterGlobal($event:any, stringVal:any) {
    this.dt!.filterGlobal(($event.target as HTMLInputElement).value, stringVal);
  }

  navigateToAddRole(){
    this.router.navigate(['/um/assign_roles'])
  }

  navigateToGrid() {
    this.router.navigate(['/um/maintain_roles']);
  }

  navigateToViewRole(id:any){
    this.router.navigate(['/um/assign_roles'],{ queryParams: { id:  id} })
  }

  navigateToUpdation(data:any) {
    this.router.navigate(['/um/update_role', data]);
  }
}
