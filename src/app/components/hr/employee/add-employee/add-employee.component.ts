import { CommonModule } from '@angular/common';
import { Component, OnInit, signal } from '@angular/core';
import { FormBuilder, FormControl, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ConfirmationService, MessageService } from 'primeng/api';
import { CalendarModule } from 'primeng/calendar';
import { DropdownModule } from 'primeng/dropdown';
import { MultiSelectModule } from 'primeng/multiselect';
import { ToastModule } from 'primeng/toast';
import { ActivatedRouterService } from '../../../../services/activated-router-service';
import { MasterDataService} from '../../../../services/master-data.service';
import { LoginService } from '../../../../services/login.service';
import { Employee} from '../../../../models/employee';
import { UserService } from '../../../../services/user.service';
import { NoSpaceDirective } from 'src/app/directives/no-space.directive';
import { AlphaNumericSpecialCharsDirective, EmployeeCodeFormatDirective } from 'src/app/directives/alphanumeric.directive';
import { AllowOnlyCharDirective } from 'src/app/directives/allow-only-char.directive';
import { AllLetterCapitalDirective, FirstLetterCapitalDirective } from 'src/app/directives/first-letter-capital.directive';
import { DisableKeysDirective } from 'src/app/directives/disable-keys.directive';
import { emailDomainValidator } from 'src/app/validators/emailDomainValidator';
import { MobileNumbersOnlyDirective } from 'src/app/directives/numbers-only.directive';
import { NoSpecialCharsDirective } from 'src/app/directives/email-no-special-char.directive';

@Component({
    selector: 'app-add-employee',
    imports: [ReactiveFormsModule, ToastModule, CalendarModule, CommonModule, DropdownModule, MultiSelectModule,
      NoSpaceDirective,FirstLetterCapitalDirective,AllowOnlyCharDirective, MobileNumbersOnlyDirective, NoSpecialCharsDirective,
      DisableKeysDirective, AllLetterCapitalDirective, AlphaNumericSpecialCharsDirective, EmployeeCodeFormatDirective
    ],
    templateUrl: './add-employee.component.html',
    styleUrls: ['./add-employee.component.scss'],
    standalone:true
})
export class AddEmployeeComponent implements OnInit{
  employeeForm!: FormGroup;
  managerList:any[]=[];
  employeeModel:Employee=new Employee();
  employeeDetails:Employee[]=[];
  employee_code:string='';
  buttonValue:string='Submit';
  employeeHeaderText='Add Employee';
  managers:string[]=[];
  // users:any[]=[];
  statusList:any[]=[];
  countries:any[]=[];
  bandGrades:any[]=[];
  departments:any[]=[];
  skillSet:any[]=[];
  todayDate: string = '';
  maxStartDate: any;
  enableRelievingDate:boolean = false;
  emailDomain = '@roboxaservices.com';
  domainAdded = false;

  constructor(
    private loginService:LoginService,
    private formBuilder: FormBuilder,
    private router: Router,
    private messageService: MessageService,private activatedRoute:ActivatedRoute,private userService:UserService,
     private activatedRouterService: ActivatedRouterService,private masterDataService:MasterDataService) {}

  ngOnInit(){
    // this.todayDate = this.getTodayDate();
    this.maxStartDate = new Date();

    this.employeeForm = this.formBuilder.group({
      employee_code:new FormControl('',[Validators.required,Validators.minLength(3), Validators.maxLength(10)]),
      name: new FormControl('', [Validators.required,Validators.minLength(3), Validators.maxLength(100)]),
      designation: new FormControl('', [Validators.required,Validators.minLength(2),Validators.maxLength(100)]),
      band_grade: new FormControl('', [Validators.required]),
      primary_skill: new FormControl('', [Validators.required]),
      secondary_skill: new FormControl(''),
      department: new FormControl('', [Validators.required]),
      email: new FormControl('', [Validators.required, Validators.email,Validators.maxLength(100), emailDomainValidator('@roboxaservices.com')]),
      mobile: new FormControl('', [Validators.required,Validators.minLength(10),Validators.maxLength(15)]),
      country: new FormControl('', [Validators.required]),
      project_specific_hire: new FormControl(''),
      contractor: new FormControl(''),
      joining_date: new FormControl('', [Validators.required]),
      relieving_date: new FormControl(''),
      manager: new FormControl(''),
      status:new FormControl('', [Validators.required])
    });
    // this.getUsers();
    this.getEmployees();
    this.activatedRoute.paramMap.subscribe(params => {
      this.employee_code = params.get('id') || '';
      if(this.employee_code){
        this.getEmployeeById();
        this.buttonValue='Update';
        this.employeeHeaderText='Edit Employee';
      }
      else{
       this.buttonValue='Submit';
       this.employeeHeaderText='Add Employee';
      }
    });
    this.getDropdownData();
  }

  handleEmailKeyDown(event: KeyboardEvent) {
    if (event.key === '@' && !this.domainAdded) {
      event.preventDefault(); // prevent default "@" input
      const ctrl = this.employeeForm.get('email');
      const currentValue = ctrl?.value || '';
      // Append domain
      ctrl?.setValue(currentValue + this.emailDomain);
      this.domainAdded = true;
    }
  }

  onEmailInput() {
    const ctrl = this.employeeForm.get('email');
    const value = ctrl?.value || '';
    // Reset the domainAdded flag if user clears or edits the domain
    this.domainAdded = value.includes(this.emailDomain);
  }
  
  getDropdownData(){
    this.loginService.getDropdownData().subscribe(data => {
      this.statusList=data.Status_List; 
      this.countries=data.countries;  
      this.departments=data.departments;
      this.bandGrades=data.BandGrades;
      this.skillSet=data.skillSet;   
    });
  }

  getEmployees(){
    this.masterDataService.getEmployeeDetails().subscribe(res=>{
      const employeeDetails=res['data'];
      // this.users = this.users.filter((user: any) => {
      //   return !employeeDetails.some((employee: any) => employee.employee_code === user.user_id);
      // });
      this.managerList = employeeDetails.map((employee: any) => ({ name: employee.name }));
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  getFormControl(formControlName:string) {
    return this.employeeForm.get(formControlName);
  }

  // getUsers(){
  //   this.userService.getMaintainUsers().subscribe(res=>{
  //     this.users=res['users'];
  //     this.users=this.users.filter((user:any)=>user.status==='active');
  //     //this.managerList = this.users.map((user: any) => ({ name: user.name }));
  //      this.getEmployees();
  //   },(err: any) => { 
  //     this.activatedRouterService.updateError(err, this.messageService)
  //   })
  // }
  getEmployeeById(){
    this.masterDataService.getEmployeeById(this.employee_code).subscribe(res=>{
      this.employeeModel=res['employee'];     
      this.employeeForm.patchValue({
        employee_code:this.employeeModel?.employee_code,
        name: this.employeeModel?.name,
        designation: this.employeeModel?.designation,
        primary_skill: this.employeeModel?.primary_skill,
        secondary_skill: this.employeeModel?.secondary_skill,
        department: this.employeeModel?.department,
        band_grade: this.employeeModel?.band_grade,
        email: this.employeeModel?.email,
        mobile: this.employeeModel?.mobile,
        country: this.employeeModel?.country,
        joining_date: new Date(this.employeeModel?.joining_date),
        manager: this.employeeModel?.manager,
        status:this.employeeModel?.status,
        project_specific_hire:this.employeeModel?.project_specific_hire,
        contractor:this.employeeModel?.contractor,
      })

      if(this.employeeForm.get('status')?.value.toLowerCase() == 'inactive') {
        this.enableRelievingDate = true;
        this.employeeForm.patchValue({
          relieving_date : new Date(this.employeeModel?.relieving_date) //new Date('2025-06-04')
        })
      }
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  setRelievingDate() {
    let status = this.employeeForm.get('status')?.value;
    if(status == 'inactive') {
      this.enableRelievingDate = true;
      this.employeeForm.controls['relieving_date']?.setValidators([Validators.required]);
    } else if(status == 'active') {
      this.employeeForm.controls['relieving_date'].clearValidators();
      this.enableRelievingDate = false;
    }
    this.employeeForm.controls['relieving_date']?.updateValueAndValidity();
  }

  onSubmit(){
    this.employeeModel.employee_code=this.employeeForm.get('employee_code')?.value;
    this.employeeModel.name=this.employeeForm.get('name')?.value;
    this.employeeModel.designation=this.employeeForm.get('designation')?.value;
    this.employeeModel.email=this.employeeForm.get('email')?.value;
    this.employeeModel.mobile=this.employeeForm.get('mobile')?.value;
    this.employeeModel.country=this.employeeForm.get('country')?.value;
    this.employeeModel.primary_skill=this.employeeForm.get('primary_skill')?.value;
    this.employeeModel.secondary_skill=this.employeeForm.get('secondary_skill')?.value;
    this.employeeModel.department=this.employeeForm.get('department')?.value;
    this.employeeModel.band_grade=this.employeeForm.get('band_grade')?.value;
    this.employeeModel.joining_date=this.changeFormat(this.employeeForm.get('joining_date')?.value);
    this.employeeModel.manager=this.employeeForm.get('manager')?.value;
    this.employeeModel.status=this.employeeForm.get('status')?.value;
    this.employeeModel.project_specific_hire=this.employeeForm.get('project_specific_hire')?.value;
    this.employeeModel.contractor=this.employeeForm.get('contractor')?.value;

    if(this.employeeModel.status == 'inactive') {
      this.employeeModel.relieving_date = this.changeFormat(this.employeeForm.get('relieving_date')?.value);
    } else if(this.employeeModel.status == 'active') {
      this.employeeModel.relieving_date = '';
    }
    console.log(this.employeeModel);
    if(this.employee_code){
      this.employeeModel.employee_code=this.employee_code;
      this.masterDataService.updateEmployee(this.employee_code,this.employeeModel).subscribe(res=>{
        this.messageService.add({ severity: 'success', summary: '', detail: 'Employee Updated Successfully' });
        setTimeout(() => {
          this.navigateToGrid()
        }, 1000);
      },(err: any) => {
        const errMsg = err?.error?.employee_code?.[0] || err?.error?.error || err?.error?.email || err; 
        this.messageService.add({ severity: 'error', summary: '', detail: errMsg });
        // this.activatedRouterService.updateError(err, this.messageService);
      })
    } else{
      this.masterDataService.addEmployee(this.employeeModel).subscribe(res=>{
        this.messageService.add({ severity: 'success', summary: '', detail: 'Employee added successfully' });
        setTimeout(() => {
          this.navigateToGrid()
        }, 1000);
      },(err: any) => {
        const errMsg = err?.error?.employee_code?.[0] || err?.error?.error || err?.error?.email || err; 
        this.messageService.add({ severity: 'error', summary: '', detail: errMsg });
      })
    }
  }

  navigateToGrid(){
    this.router.navigate(['/hr/employees']);
  }

  changeFormat(dateToTransfer:string){
    const date = new Date(dateToTransfer);
    const formattedDate = date.getFullYear() + '-' +
      String(date.getMonth() + 1).padStart(2, '0') + '-' +
      String(date.getDate()).padStart(2, '0');
    return formattedDate
  }

  back(){
    this.employee_code ? this.router.navigate(['/hr/employees'],{ queryParams: { id: this.employee_code} }):this.router.navigate(['/hr/employees']);
   }

  //  onChangeEmployeeCode(){
  //    const name=this.users.find((user)=> user.user_id == this.employeeForm.get('employee_code')?.value).name;
  //    this.employeeForm.get('name')?.setValue(name);
  //  }
}
