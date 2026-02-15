import { CommonModule } from '@angular/common';
import { Component, OnInit, ViewChild,ChangeDetectorRef } from '@angular/core';
import { Table, TableModule } from 'primeng/table';
import { IconFieldModule } from 'primeng/iconfield';
import { InputIconModule } from 'primeng/inputicon';
import { ActivatedRoute, Router } from '@angular/router';
import { ConfirmationService, MessageService } from 'primeng/api'
import { ToastModule } from 'primeng/toast';
import { DialogModule } from 'primeng/dialog';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { BadgeModule } from 'primeng/badge';
import { MultiSelectModule } from 'primeng/multiselect';
import { CheckboxModule } from 'primeng/checkbox';
import { DropdownModule } from 'primeng/dropdown';
import { FormBuilder, FormControl, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { LoginService } from '../../../services/login.service';
import { UserService } from '../../../services/user.service';
import { ActivatedRouterService } from '../../../services/activated-router-service';
import { User_Roles} from '../../../models/user';

interface Role {
  id: number;
  role_name: string[];
}

@Component({
    selector: 'app-assign-role',
    imports: [ReactiveFormsModule, TableModule, CommonModule, InputIconModule, IconFieldModule, ToastModule, DialogModule,
      ConfirmDialogModule, CheckboxModule, FormsModule, DropdownModule, BadgeModule,MultiSelectModule],
    templateUrl: './assign-role.component.html',
    styleUrls: ['./assign-role.component.scss'],
    standalone:true,
    providers: [ConfirmationService, MessageService]
})
export class AssignRoleComponent implements OnInit{
  assignForm!: FormGroup;
  usersList:any[] = [];
  users:any = [];
  @ViewChild('dt2') dt : Table | undefined;
  userModel:User_Roles=new User_Roles();
  roles:Role[]=[];
  selectedUser:any = {};
  selectedRoleId:string = '';
  selectedRoles:string[] = [];
  userId:string='';
  userRoles:any;
  rolesData:any[]=[];
  isRoleExists:boolean=false;
  isRoleId:boolean=false;
  buttonValue:string='Submit';
  isUsersLoading:boolean = true;

  constructor(private cdRef: ChangeDetectorRef,
    private formBuilder: FormBuilder,
    private router: Router,
    private messageService: MessageService,
    private loginService: LoginService,
    private userService:UserService,
    private activatedRoute:ActivatedRoute,
    private activatedRouterService: ActivatedRouterService
  ) {}

  ngOnInit(): void {
      this.buildForm();
      this.usersList=[];
      this.selectedRoles=[];
      this.activatedRoute.queryParams.subscribe((res) => {
        this.userId=res['id']
      });
      this.getRoles();    
      //this.getAssignRoles();
      if(this.userId){
        this.buttonValue='Update';
        this.getAssignRolesByUserId();
      }
      else{
        this.buttonValue='Submit';
       this.getMaintainUsers();
      }  
    }
  
  buildForm(){
    this.assignForm = this.formBuilder.group({
      userId: new FormControl('', [Validators.required]),
      name:new FormControl(''),
      email: new FormControl('', []),
      mobile: new FormControl('', []),
      startDate: new FormControl('', []),
      endDate: new FormControl('', []),
      last_login: new FormControl('', []),
      status: new FormControl('', []),
      roleId: new FormControl('', [Validators.required]),
    })
  }

  getRoles(){
   this.userService.getRoles().subscribe(data=>{
    this.roles=data['roles'];
   });
  }

  applyFilterGlobal($event:any, stringVal:any) {
    this.dt!.filterGlobal(($event.target as HTMLInputElement).value, stringVal);
  }

  getAssignRolesByUserId(){
    this.assignForm.reset();
    this.userService.getAssignRolesByUserId(this.userId).subscribe(res=>{
      this.usersList.push(res.user);
      this.assignForm.controls['userId'].setValue(res.user?.user_id);
      this.getUserDetailsByUsername(this.userId);
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  getMaintainUsers(){
    this.assignForm.reset();
    this.isUsersLoading = true;
    this.userService.getMaintainUsers().subscribe((res:any) => {
      this.usersList = res?.['users'];
      this.usersList=this.usersList.filter(role=> (role.role_name==null || role.role_name?.length==0) && role.status=='active');
      this.users = this.usersList.map((user:any) => {
        return {name:user.name, value:user.user_id};
      })
      this.isUsersLoading = false;
    })
  }

  getUserDetailsByUsername(event:any) {
  this.cdRef.detectChanges();
    const userId=this.assignForm.get('userId')?.value;
    this.isRoleId=this.assignForm.get('userId')?.value ? true:false;
    this.selectedUser = this.usersList.find((user:any) => user.user_id === userId);
    this.userModel=this.selectedUser;
    this.assignForm.patchValue({
      userId:userId,
      name: this.selectedUser.name || '-',
      mobile: this.selectedUser.mobile || '-',
      email: this.selectedUser.email || '-',
      last_login: this.formatLastLogin(this.selectedUser.last_login),
      startDate: this.selectedUser.start_date || '-',
      endDate: this.selectedUser.end_date || '-',
      status: (this.selectedUser.status=='active'? 'Active' : 'In Active'),
      roleId:this.selectedUser.role_name
    });
    const selectedUserRoles=this.usersList.filter(user=>user.user_id==userId);
    this.userRoles=selectedUserRoles.find(r=>r.role_name)?.role_name;
    this.selectedRoles=this.userRoles;
  }

  getFormValidation() {
    return this.assignForm.controls['userId'].value &&
    this.assignForm.controls['email'].value &&
    this.assignForm.controls['name'].value && 
    this.assignForm.controls['startDate'].value &&
    this.assignForm.controls['endDate'].value &&
    this.assignForm.controls['status'].value && 
    this.assignForm.controls['last_login'].value && 
    this.assignForm.controls['mobile'].value && 
    (this.assignForm.controls['roleId'].value || this.selectedRoles?.length>0)
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

  addRole(event: any) {
    this.selectedRoles = event?.value; 
  }

  hasNoRoles(user: User_Roles): boolean {
    return Array.isArray(user?.role_name) && user?.role_name?.length === 0;
  }
  
  back(){
    this.router.navigate(['/um/maintain_roles']);
  }

  changeFormat(dateToTransfer:string){
    const date = new Date(dateToTransfer);
    const formattedDate = date.getFullYear() + '-' +
      String(date.getMonth() + 1).padStart(2, '0') + '-' +
      String(date.getDate()).padStart(2, '0');
    return formattedDate
  }

  getFormControl(formControlName:string) {
    return this.assignForm.get(formControlName);
  }

  onChangeUser(){
    const name=this.usersList.find(user=>user.user_id==this.assignForm.controls['userId'].value).name;
    this.assignForm.controls['name'].setValue(name);
  }

  onSubmit() {
    const rolesRequestData = {
        "user_id": this.userModel.user_id,
        "role_name": this.selectedRoles ,  // Default roles if none selected
        "name": this.userModel.name,
        "email": this.userModel.email,
        "mobile": this.userModel.mobile,
        "start_date": this.changeFormat(this.userModel.start_date),
        "end_date": this.changeFormat(this.userModel.end_date),
        "status": this.userModel.status,
        "last_login": this.changeFormat(this.userModel.last_login)
    };

    if (this.userRoles?.length > 0) {
        // If roles are being updated, make the update API call
        this.userService.updateAssignUserRoles(rolesRequestData, this.userModel.user_id).subscribe(
            (response: any) => {
                this.messageService.add({
                    severity: 'success',
                    summary: '',
                    detail: 'Updated User Roles Successfully'
                });
                setTimeout(() => {
                    this.back();
                }, 1000);
            },
            (error: any) => {
                this.activatedRouterService.updateError(error, this.messageService);
            }
        );
    } else {
        // If new roles are being assigned, make the create API call
        this.userModel.role_name = rolesRequestData.role_name;
        this.userModel.last_login = this.changeFormat(this.userModel.last_login);

        this.userService.assignUserRoles(this.userModel).subscribe(
            (response: any) => {
                this.messageService.add({
                    severity: 'success',
                    summary: '',
                    detail: 'Assigned User Roles Successfully'
                });
                setTimeout(() => {
                    this.back();
                }, 1000);
            },
            (error: any) => {
                this.activatedRouterService.updateError(error, this.messageService);
            }
        );
    }
}
}
