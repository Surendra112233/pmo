import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormBuilder, FormControl, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { MessageService } from 'primeng/api';
import { CalendarModule } from 'primeng/calendar';
import { DropdownModule } from 'primeng/dropdown';
import { TableModule } from 'primeng/table';
import { ToastModule } from 'primeng/toast';
import { ActivatedRouterService } from 'src/app/services/activated-router-service';
import { EmployeeService } from 'src/app/services/employee.service';
import { LoginService } from 'src/app/services/login.service';
import { MasterDataService } from 'src/app/services/master-data.service';
import { TravelService } from 'src/app/services/travel.service';

@Component({
  selector: 'app-raise-cash-advance-request',
  templateUrl: './raise-cash-advance-request.component.html',
  styleUrls: ['./raise-cash-advance-request.component.scss'],
    imports: [ToastModule, DropdownModule, ReactiveFormsModule, CalendarModule,
        TableModule, CommonModule, FormsModule],
    standalone: true
})
export class RaiseCashAdvanceRequestComponent {
  requestForm!: FormGroup;
  requestId: any;
  requstsList: any;
  constructor(
        private loginService: LoginService,
        private formBuilder: FormBuilder,
        private router: Router,
        private messageService: MessageService, private activatedRoute: ActivatedRoute, private empService: EmployeeService,
        private activatedRouterService: ActivatedRouterService, private masterDataService: MasterDataService,
        private travelService: TravelService
      ) { }
 ngOnInit() {
  this.requestForm = this.formBuilder.group({
        requestId: new FormControl('', Validators.required),
        employee_code: new FormControl(''),
        employee_name: new FormControl(''),
        department: new FormControl(''),
        project_type: new FormControl(''),
        project_code: new FormControl(''),
        project_name: new FormControl(''),
        country: new FormControl(''),
        sbu_head: new FormControl(''),
        delivery_manager: new FormControl(''),
        project_manager: new FormControl(''),
        travel_location: new FormControl(''),
        travel_purpose: new FormControl(''),
        others_specify: new FormControl(''),
        status: new FormControl(''),
        travel_preferences: new FormControl(''),
        date_of_birth: new FormControl(''),
        age: new FormControl(''),
        id_document_type: new FormControl(''),
        id_document_number: new FormControl(''),
        passport_number: new FormControl(''),
        mobile: new FormControl(''),
        alt_mobile: new FormControl(''),
        email: new FormControl(''),
        alt_email: new FormControl(''),
        address: new FormControl(''),
        comments: new FormControl(''),
    });
    this.getRequests()
 }

 getFormControl(formControlName: string) {
    return this.requestForm.get(formControlName);
  }

  getRequests(){
      this.travelService.getAllRequests().subscribe((res) => {
        console.log('all requests',res);
        this.requstsList = res;
      },(err: any) => { 
        this.activatedRouterService.updateError(err, this.messageService)
      })
  }

 navigateToGrid(){
  this.router.navigate(['/travel/travel-requests']);
 }

 selectedRequestId(event:any){
  console.log('selected reqId',event)
  this.requestId = event.value
  this.getRequestedIdData(this.requestId)
 }

 getRequestedIdData(id:any){
   this.travelService.getTravelDetailsByRequestId(id).subscribe(res=>{
      this.patchRequestData(res)
    },(err: any) => { 
        this.activatedRouterService.updateError(err, this.messageService)
  })
 }

 patchRequestData(response: any) {
    this.requestForm.patchValue({
      employee_code: response.employee_code,
      employee_name: response.employee_name,
      department: response.department,
      project_type: response.project_type,
      project_code: response.project_code,
      project_name: response.project_name,
      project_manager: response.project_manager,
      delivery_manager: response.delivery_manager,
      sbu_head: response.sbu_head,
      travel_location: response.travel_location,
      travel_purpose: response.travel_purpose,
      others_specify: response.others_specify,
      travel_preferences: response.travel_preferences,
      accommodation_required: response.accommodation_required ? 'Yes' : 'No',
      status: response.status,
      country: response.country
    });
  }

 submit(){

 }
}
