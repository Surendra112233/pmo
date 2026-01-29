import { CommonModule } from '@angular/common';
import { Component, signal } from '@angular/core';
import { FormBuilder, FormControl, FormGroup, Validators, ReactiveFormsModule,AbstractControl, ValidatorFn, ValidationErrors } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ConfirmationService, MessageService } from 'primeng/api';
import * as moment from 'moment';
import 'moment-timezone';
import { UserService } from '../../../services/user.service';
import { ActivatedRouterService } from '../../../services/activated-router-service';
import { User} from '../../../models/user';
import { LoginService} from '../../../services/login.service';
import { ToastModule } from 'primeng/toast';
import { CalendarModule } from 'primeng/calendar';
import { DropdownModule } from 'primeng/dropdown';
import { NoSpaceDirective} from 'src/app/directives/no-space.directive';
import { MobileNumbersOnlyDirective } from 'src/app/directives/numbers-only.directive';
import { AllowOnlyCharDirective } from 'src/app/directives/allow-only-char.directive';
import{emailDomainValidator} from 'src/app/validators/emailDomainValidator';
import { NoSpecialCharsDirective } from 'src/app/directives/email-no-special-char.directive';
import { FirstLetterCapitalDirective } from 'src/app/directives/first-letter-capital.directive';
import { DisableKeysDirective } from 'src/app/directives/disable-keys.directive';
import { MasterDataService } from 'src/app/services/master-data.service';
import { BadgeModule } from 'primeng/badge';
import { MultiSelectModule } from 'primeng/multiselect';

@Component({
    selector: 'app-user-registration',
    standalone:true,
    imports: [ReactiveFormsModule, ToastModule, CalendarModule, CommonModule, DropdownModule,NoSpaceDirective,
      AllowOnlyCharDirective, CalendarModule, 
      NoSpecialCharsDirective, FirstLetterCapitalDirective, DisableKeysDirective, BadgeModule,MultiSelectModule, MobileNumbersOnlyDirective],
    templateUrl: './user-registration.component.html',
    styleUrls: ['./user-registration.component.scss'],
    providers: [ConfirmationService, MessageService]
})
export class UserRegistrationComponent {
  userForm!: FormGroup;
  isAPICallInProgress = signal<boolean>(false);
  statusList: any[]=[];  
  timezones: { label: string; value: string }[] = [];
  userModel:User=new User();
  buttonValue:string='Submit';
  userId:string='';
  fullUserId: string = '';
  minEndDate:any;
  maxStartDate:any;
  joiningDate:any;
  lastLogin:string = '-';
  users:any = [];
  employees:any = [];
  allEmployees:any = [];
  isUsersLoading:boolean = true;

  constructor(
    private userService:UserService,
    private formBuilder: FormBuilder,
    private router: Router,
    private messageService: MessageService,
    private activatedRoute:ActivatedRoute,private loginService:LoginService,
     private activatedRouterService: ActivatedRouterService,
     private masterDataService: MasterDataService
  ) {}
  
  ngOnInit() {
    this.maxStartDate = new Date();
    const futureDate = new Date();
    futureDate.setFullYear(futureDate.getFullYear() + 25);

    this.userForm = this.formBuilder.group({
      name: new FormControl('', [Validators.required,Validators.minLength(3),Validators.maxLength(100)]), 
      user_id: new FormControl('', [Validators.required,Validators.maxLength(7)]),
      email: new FormControl('', [Validators.required, Validators.email,Validators.maxLength(100), emailDomainValidator('@roboxaservices.com')]),
      mobile: new FormControl('', [Validators.required,Validators.minLength(10),Validators.maxLength(15)]),
      start_date: new FormControl('', [Validators.required]),
      end_date: new FormControl(futureDate, [Validators.required]),
      status: new FormControl('active',[Validators.required]),
    }, { validators: this.dateValidator });
    
    this.getEmployees();
    
    this.activatedRoute.paramMap.subscribe(params => {
      this.userId = params.get('id') || '';
      if(this.userId){
        this.getDataById();
        this.buttonValue='Update';
      }
      else{
       this.buttonValue='Submit';
      }
    });

    this.timezones = moment.tz.names().map(zone => {
      const offset = moment.tz(zone).format('Z');
      return {
        label: `(UTC${offset}) ${zone}`,
        value: zone
      };
    });

    this.userForm.get('start_date')?.valueChanges.subscribe(() => {
      this.userForm.updateValueAndValidity();
    });
  
    this.userForm.get('end_date')?.valueChanges.subscribe(() => {
      this.userForm.updateValueAndValidity();
    });
  
  }

  getEmployees(){
    this.masterDataService.getEmployeeDetails().subscribe(res=>{
      this.employees =res['data'];
      this.employees.sort((a:any, b:any) => a.employee_code.localeCompare(b.employee_code));
      this.allEmployees = res['data'];
      this.getUsers();
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  getUsers(){
    this.isUsersLoading = true;
    this.userService.getMaintainUsers().subscribe(res=>{
      this.users=res['users'];
      this.employees = this.employees.filter((emp: any) => {
        return !this.users.some((user: any) =>user.user_id === emp.employee_code );
      });
      
      if(this.userId){
        //set start date equal to joining date in edit mode
        this.joiningDate = this.allEmployees.find((emp:any)=> emp.employee_code == this.userForm.get('user_id')?.value).joining_date;
        this.joiningDate = new Date(this.joiningDate)
      }
      this.isUsersLoading = false;
      
    },(err: any) => { 
      this.isUsersLoading = false;
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  onChangeEmployeeCode(){
    const emp = this.employees.find((emp:any)=> emp.employee_code == this.userForm.get('user_id')?.value);
    // const joining_date=this.employees.find((emp:any)=> emp.employee_code == this.userForm.get('user_id')?.value).joining_date;
    if(emp) {
      this.joiningDate = new Date(emp.joining_date);
      this.userForm.get('name')?.setValue(emp.name);
      this.userForm.get('email')?.setValue(emp.email);
      this.userForm.get('mobile')?.setValue(emp.mobile);
    }
  }

  preventPaste(event:any) {
    event.preventDefault();
  }

  get userType() {
    return this.userForm.get('userType')?.value;
  }

  navigateToGrid() {
    this.router.navigate(['/um/maintain_users']);
  }

  getFormControl(formControlName:string) {
    return this.userForm.get(formControlName);
  }

  getFormValidation() {
    const controls = this.userForm.controls;  
    const basicFieldsValid =  controls['name'].value &&
                              controls['email'].value &&
                              controls['mobile'].value &&
                              controls['start_date'].value &&
                              controls['end_date'].value &&
                              controls['user_id'].value &&
                              controls['status'].value
    // console.log(this.userForm)
    return basicFieldsValid;
  }  
  
  dateValidator(control: AbstractControl): ValidationErrors | null {
    const startDate = control.get('start_date')?.value;
    const endDate = control.get('end_date')?.value;

    if (startDate && endDate) {
        const start = new Date(startDate);
        const end = new Date(endDate);

        // Compare year, month, and day
        if (end.getTime() <= start.getTime()) {
            return { endDateLessThanStartDate: true };
        }
    }
    return null;
  }

  changeFormat(dateToTransfer:string){
    const date = new Date(dateToTransfer);
    const formattedDate = date.getFullYear() + '-' +
      String(date.getMonth() + 1).padStart(2, '0') + '-' +
      String(date.getDate()).padStart(2, '0');
    return formattedDate
  }

  getDataById(){
    this.userService.getUserDataById(this.userId).subscribe(res=>{
      this.userModel=res.user;
      this.lastLogin = this.userModel.last_login || '-';
      this.userForm.patchValue({
        user_id:res.user?.user_id,
        name: res.user?.name,
        email: res.user?.email,
        mobile: res.user?.mobile,
        start_date:new Date(res.user?.start_date),
        end_date: new Date(res.user?.end_date),
        status: res.user?.status=='active' ? 'active' : 'inactive'
      })
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })
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

  onSubmit() {
    this.userModel.user_id=this.userForm.get('user_id')?.value;
    this.userModel.name=this.userForm.get('name')?.value;
    this.userModel.email=this.userForm.get('email')?.value;
    this.userModel.mobile=this.userForm.get('mobile')?.value;
    this.userModel.start_date=this.changeFormat(this.userForm.get('start_date')?.value);
    this.userModel.end_date=this.changeFormat(this.userForm.get('end_date')?.value);
    this.userModel.status= this.userForm.get('status')?.value;

    this.messageService.clear();
    if(this.userId){
      this.userModel.user_id=this.userId;
      this.userService.updateUser(this.userId,this.userModel).subscribe(res=>{
        this.messageService.add({ severity: 'success', summary: '', detail: 'User Updated Successfully' });
        setTimeout(() => {
          this.navigateToGrid()
        }, 1000);
      },(err: any) => { 
        const errMsg = err?.error?.error || err?.error?.user_id?.[0] || err;
        this.messageService.add({ severity: 'error', summary: '', detail: errMsg });
      })
    }
    else{
      this.userModel.status='active';
     this.userService.createUser(this.userModel).subscribe(
      data=>{
      this.messageService.add({ severity: 'success', summary: '', detail: 'User Created Successfully' });
      setTimeout(() => {
        this.navigateToGrid()
      }, 1000);
    },(err: any) => {
      const errMsg = err?.error?.error || err?.error?.user_id?.[0] || err;
      this.messageService.add({ severity: 'error', summary: '', detail: errMsg });
    });
    }     
  }

  back(){
    this.userId ? this.router.navigate(['/um/view_user'],{ queryParams: { id: this.userId} }):this.router.navigate(['/um/maintain_users']);
  }

  testEnddate(end_date:any,start_date:any){
    this.dateValidator(this.userForm);
    if(start_date.value>end_date.value){
    // this.messageService.add({ severity: 'error', summary: 'Date validation Error', detail: 'End date must be greater than start date.' });
    }
  }
}
