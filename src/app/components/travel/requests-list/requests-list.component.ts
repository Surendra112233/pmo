import { CommonModule } from '@angular/common';
import { Component, ViewChild } from '@angular/core';
import { Router } from '@angular/router';
import { MessageService } from 'primeng/api';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { DialogModule } from 'primeng/dialog';
import { IconFieldModule } from 'primeng/iconfield';
import { InputIconModule } from 'primeng/inputicon';
import { Table, TableModule } from 'primeng/table';
import { ToastModule } from 'primeng/toast';
import { ActivatedRouterService } from 'src/app/services/activated-router-service';
import { TravelService } from 'src/app/services/travel.service';
import { UserService } from 'src/app/services/user.service';

@Component({
  selector: 'app-requests-list',
  templateUrl: './requests-list.component.html',
  styleUrls: ['./requests-list.component.scss'],
  imports: [TableModule, CommonModule, InputIconModule, IconFieldModule, ToastModule, DialogModule,
        ConfirmDialogModule],
  standalone:true
})
export class RequestsListComponent {
    @ViewChild('dt2') dt : Table | undefined
    
    roles:any[] = [];
  
    constructor(
      private userService:UserService,
      private router:Router,    
      private messageService: MessageService,
      private activatedRouterService: ActivatedRouterService,
      private travelService: TravelService
    ) {}
  
    ngOnInit(){
      this.getRequests()
    }
  
    getRequests(){
      this.travelService.getAllRequests().subscribe((res) => {
        console.log('all requests',res);
        this.roles = res;
      },(err: any) => { 
        this.activatedRouterService.updateError(err, this.messageService)
      })
    }
  
    applyFilterGlobal($event:any, stringVal:any) {
      this.dt!.filterGlobal(($event.target as HTMLInputElement).value, stringVal);
    }
  
    navigateToCreate(){
      this.router.navigate(['/travel/raise-travel-request']);
    }
  
    navigateToGrid() {
      this.router.navigate(['/um/maintain_roles']);
    }
  
    navigateToViewRole(id:any){
      this.router.navigate(['/travel/view-travel-request'],{ queryParams: { id:  id} })
    }
  
    navigateToUpdation(data:any) {
      this.router.navigate(['/um/update_role', data]);
    }
}
