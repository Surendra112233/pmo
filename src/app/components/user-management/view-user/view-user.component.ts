import { Component, OnInit } from '@angular/core';
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
import { User } from 'src/app/models/user';

@Component({
    selector: 'app-view-user',
    imports: [ToastModule, CommonModule, ReactiveFormsModule, CalendarModule, FormsModule, CheckboxModule, RadioButtonModule],
    templateUrl: './view-user.component.html',
    styleUrls: ['./view-user.component.scss'],
    standalone:true,
    providers: [MessageService]
})
export class ViewUserComponent implements OnInit{
  userName:string = '';
  userId:string='';
  userModel:User=new User();
  constructor(
    private router:Router,
    private formBuilder:FormBuilder,
    private activatedRoute:ActivatedRoute,
    private userService:UserService,private messageService: MessageService,
        private activatedRouterService: ActivatedRouterService
  ) {}

  ngOnInit(): void {
    this.activatedRoute.queryParams.subscribe((res) => {
      this.userId=res['id']
    })

    this.getData()
  }

  getData(){
    this.userService.getUserDataById(this.userId).subscribe(res=>{
      this.userName=res.user?.name;
      this.userModel=res.user;
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  navigateToGrid() {
    this.router.navigate(['/um/maintain_users']);
  }

  navigateToEditUser() {
    this.router.navigate(['/um/edit_user',this.userId]);
  }
  changeFormat(dateToTransfer:string){
    const date = new Date(dateToTransfer);
    const formattedDate = date.getFullYear() + '-' +
      String(date.getMonth() + 1).padStart(2, '0') + '-' +
      String(date.getDate()).padStart(2, '0');
    return formattedDate
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
