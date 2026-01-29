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
import { UserService } from '../../../services/user.service';
import { ActivatedRouterService } from '../../../services/activated-router-service';

@Component({
    selector: 'app-maintain-user-grid',
    imports: [TableModule, CommonModule, InputIconModule, IconFieldModule, ToastModule, DialogModule,
      ConfirmDialogModule, CheckboxModule, FormsModule, ReactiveFormsModule],
    templateUrl: './maintain-user-grid.component.html',
    styleUrls: ['./maintain-user-grid.component.scss'],
    standalone:true,
    providers: [ConfirmationService, MessageService]
})
export class MaintainUserGridComponent {
  @ViewChild('dt2') dt : Table | undefined
  users:any[]=[];
  selectedUserRow:any;
  displayDeleteDialog:boolean=false;
  constructor(
    private userService:UserService,
    private router:Router,    
    private messageService: MessageService,
    private activatedRouterService: ActivatedRouterService
  ) {}

    status = [
    {id:'all', name: 'All'},
    {id:'active', name: 'Active'},
    {id:'inactive', name: 'Inactive'}
  ];
  selectedStatus = 'active';
  filteredData:any = [];

  ngOnInit(){
    this.getUsers()
  }

  getUsers(){
    this.userService.getMaintainUsers().subscribe(res=>{
      this.users=res['users']
      this.users.sort((a, b) => {
        // Convert start_date to Date objects and subtract
        // const dateA = new Date(a.last_login);
        // const dateB = new Date(b.last_login);        
        // return dateB.getTime() - dateA.getTime(); 
        const dateA = new Date(a.updated_at || a.created_at).getTime();
        const dateB = new Date(b.updated_at || b.created_at).getTime();
        return dateB - dateA; // Descending order
      });
      this.filterUsersByStatus();
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }
    filterUsersByStatus() {
    if (this.selectedStatus === 'all') {
      this.filteredData = [...this.users];
    } else {
      this.filteredData = this.users.filter(
        (emp:any) => emp.status.toLowerCase() === this.selectedStatus
      );
    }
  }

  applyFilterGlobal($event:any, stringVal:any) {
    this.dt!.filterGlobal(($event.target as HTMLInputElement).value, stringVal);
  }

  navigateToGrid() {
    this.router.navigate(['/um/maintain_users']);
  }

  navigateToRegistration() {
    this.router.navigate(['/um/user_registration']);
  }

  navigateToView(id:string) {
    this.router.navigate(['/um/view_user'], { queryParams: { id:  id} });
  }

  deleteUser(){
    this.selectedUserRow.status='inactive';
   this.userService.updateUser(this.selectedUserRow.user_id,this.selectedUserRow).subscribe(res=>{
    this.displayDeleteDialog = false;
    this.messageService.add({ severity: 'success', summary: '', detail: 'User is deactivated successfully' });
    setTimeout(() => {
      this.navigateToGrid()
    }, 1000);
  },(err: any) => { 
    this.activatedRouterService.updateError(err, this.messageService)
  })
  }

  showDeleteDialog(user:any){
    this.displayDeleteDialog = true;
    this.selectedUserRow=user;
  }

  closeDeleteDialog() {
    this.displayDeleteDialog = false;
    this.selectedUserRow=null;
  }

  formatLastLogin(timestamp: string): string {
    if (!timestamp) {
      return 'NA';
    }

    const date = new Date(timestamp);
    if (isNaN(date.getTime())) {
      return 'NA'; // Handle invalid timestamps
    }

    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0'); // Ensure 2-digit month
    const day = String(date.getDate()).padStart(2, '0'); // Ensure 2-digit day
    const hours = String(date.getHours()).padStart(2, '0'); // Ensure 2-digit hours
    const minutes = String(date.getMinutes()).padStart(2, '0'); // Ensure 2-digit minutes
    const seconds = String(date.getSeconds()).padStart(2, '0'); // Ensure 2-digit seconds
  
    return `${day}-${month}-${year} ${hours}:${minutes}:${seconds}`;
  }
  
}