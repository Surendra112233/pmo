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
import { Employee } from '../../../../models/employee';
@Component({
    selector: 'app-view-employee',
    imports: [ToastModule, CommonModule, ReactiveFormsModule, CalendarModule, FormsModule, CheckboxModule, RadioButtonModule],
    templateUrl: './view-employee.component.html',
    styleUrls: ['./view-employee.component.scss'],
    providers: [MessageService],
    standalone:true
})
export class ViewEmployeeComponent implements OnInit{
  employee_code:string='';
 // employeeForm!: FormGroup;
  employee:Employee=new Employee();
  constructor(
    private router:Router,
    private formBuilder:FormBuilder,
    private activatedRoute:ActivatedRoute,
    private masterDataService:MasterDataService,private messageService: MessageService,
        private activatedRouterService: ActivatedRouterService
  ) {}

  ngOnInit(){
    // this.employeeForm = this.formBuilder.group({
    //   employee_code: new FormControl(''),
    //   name: new FormControl(''),
    //   designation: new FormControl(''),
    //   band_grade: new FormControl(''),
    //   country: new FormControl(''),
    //   joining_date: new FormControl(''),
    //   manager: new FormControl(''),   
    // })

    this.activatedRoute.queryParams.subscribe((res) => {
      this.employee_code=res['id']
    })
    this.getEmployeeById()
  }

  getEmployeeById(){
    this.masterDataService.getEmployeeById(this.employee_code).subscribe(res=>{
      this.employee=res['employee'];
     //const employeeDetails=this.employee.find(task=>task.employee_code==this.employee_code);
      // this.employeeForm.patchValue({
      //   employee_code:this.employee?.employee_code,
      //   name: this.employee?.name,
      //   designation: this.employee?.designation,
      //   band_grade: this.employee?.band_grade,
      //   country: this.employee?.country,
      //   joining_date: this.employee?.joining_date,
      //   manager: this.employee?.manager
      // })
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  navigateToGrid() {
    this.router.navigate(['/hr/employees'],{ queryParams: { id: this.employee_code}});
  }

  navigateToEditEmployee() {    
    this.router.navigate(['/hr/edit_employee',this.employee_code]);
  }

}



