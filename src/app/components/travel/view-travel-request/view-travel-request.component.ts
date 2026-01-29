import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormArray, FormBuilder, FormControl, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
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
  selector: 'app-view-travel-request',
  templateUrl: './view-travel-request.component.html',
  styleUrls: ['./view-travel-request.component.scss'],
  imports: [ToastModule, DropdownModule, ReactiveFormsModule, CalendarModule,
      TableModule, CommonModule, FormsModule],
  standalone: true
})
export class ViewTravelRequestComponent {
requestForm!: FormGroup;
approverForm!: FormGroup;
  projectTypeList: any = [];
  phaseList: any = [];
  selectedProjectType: any;
  projectCodeList: any = [];
  countriesList: any = [];
  travelPurpose: any = [];
  travelLocation: any = [];
  travelModes: any = [];
  paymentsBy: any = [];
  idTypes: any = [];
  acTypes: any = [];
  paymentDebitedTo: any = [];
  employeeCode: any;
  role: any;
  today: Date = new Date();
  requestId:string='';
  requestData:any;
  approvalHistory = [
    {
      status: 'CREATED',
      role: 'Employee',
      user: 'CH Bhanu Prakash Varma',
      date: '2025-12-16',
      time: '09:00',
      comments: 'Initial travel request submitted'
    },
    {
      status: 'APPROVED',
      role: 'Project Manager',
      user: 'Rama Krishna',
      date: '2025-12-16',
      time: '11:30',
      comments: 'Reviewed and approved'
    },
    {
      status: 'REJECTED',
      role: 'SBU Head',
      user: 'SBU Head',
      date: '2025-12-17',
      time: '10:15',
      comments: 'Budget constraints. Please revise'
    }
  ];
  constructor(
      private loginService: LoginService,
      private formBuilder: FormBuilder,
      private router: Router,
      private messageService: MessageService, private activatedRoute: ActivatedRoute, private empService: EmployeeService,
      private activatedRouterService: ActivatedRouterService, private masterDataService: MasterDataService,
      private travelService: TravelService
    ) { }
  
  ngOnInit() {
    this.employeeCode = localStorage.getItem('userId');
    const roleStr = localStorage.getItem('Roles'); 
    this.role = roleStr ? roleStr.split(',') : [];
    this.requestForm = this.formBuilder.group({
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
        travel_details: this.formBuilder.array([]),
        travel_preferences: new FormControl(''),
        accommodation_required: [false],  // yes/no or boolean
        accommodation: this.formBuilder.array([]),
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
    this.approverForm = this.formBuilder.group({
      "project_manager_comments": new FormControl(''),
      "deliver_manager_comments": new FormControl(''),
      "sbu_head_comments": new FormControl(''),
      "finance_comments": new FormControl(''),
      "travel_comments": new FormControl(''),
      "hr_comments": new FormControl('')
    });
    this.activatedRoute.queryParams.subscribe((res) => {
      this.requestId=res['id']
    })
    this.getRequestedData()
  }

  get travelDetails(): FormArray {
      return this.requestForm.get('travel_details') as FormArray;
  }

  get accommodations(): FormArray {
    return this.requestForm.get('accommodation') as FormArray;
  }

  hasApprovalRole(): boolean {
    const approvalRoles = ['Manager', 'DeliveryHead', 'SBUHead'];
    return this.role.some((role:any) => approvalRoles.includes(role));
  }

  isOnlyEmployee(): boolean {
    return this.role.length === 1 && this.role.includes('Employee');
  }


  createTravelRow(): FormGroup {
    return this.formBuilder.group({
      departure_country: [''],
      departure_from: [''],
      departure_date: [''],
      departure_time: [''],
      arrival_country: [''],
      arrival_to: [''],
      arrival_date: [''],
      arrival_time: [''],
      mode: [''],
      payment_by: ['']
    });
  }

  createAccommodationRow(): FormGroup {
    return this.formBuilder.group({
      accommodation_type: [''],
      check_in: [''],
      check_out: [''],
      no_of_days: [''],
      city: [''],
      payment_to: [''],
      remarks: ['']
    });
  }

  formatDate(date: string): string {
    if (!date) return '';
    const d = new Date(date);
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    return `${day}/${month}/${year}`;
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
    if (response.personal_details) {
      this.requestForm.patchValue({
        date_of_birth: response.personal_details.date_of_birth,
        age: response.personal_details.age,
        id_document_type: response.personal_details.id_document_type,
        id_document_number: response.personal_details.id_document_number,
        passport_number: response.personal_details.passport_number,
        mobile: response.personal_details.mobile,
        alt_mobile: response.personal_details.alt_mobile,
        email: response.personal_details.email,
        alt_email: response.personal_details.alt_email,
        address: response.personal_details.address,
        comments: response.personal_details.comments
      });
    }
    this.travelDetails.clear();
    response.travel_details.forEach((td:any) => {
      const row = this.createTravelRow();
      row.patchValue({
        departure_country: td.departure_country,
        departure_from: td.departure_from,
        departure_date: td.departure_date,
        departure_time: td.departure_time,
        arrival_country: td.arrival_country,
        arrival_to: td.arrival_to,
        arrival_date: td.arrival_date,
        arrival_time: td.arrival_time,
        mode: td.mode,
        payment_by: td.payment_by
      });
      this.travelDetails.push(row);
    });

    // 🔹 Patch Accommodation (FormArray)
    this.accommodations.clear();
    response.accommodation.forEach((ac:any) => {
      const row = this.createAccommodationRow();
      row.patchValue({
        accommodation_type: ac.accommodation_type,
        check_in: ac.check_in,
        check_out: ac.check_out,
        no_of_days: ac.no_of_days,
        city: ac.city,
        payment_to: ac.payment_to,
        remarks: ac.remarks
      });
      this.accommodations.push(row);
    });
  }

  getRequestedData(){
    this.travelService.getTravelDetailsByRequestId(this.requestId).subscribe(res=>{
      this.requestData =  res
      this.patchRequestData(res)
    },(err: any) => { 
        this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  navigateToGrid() {
    this.router.navigate(['/travel/travel-requests']);
  }

  navigateToEditRequest(){
    this.router.navigate(['/travel/edit_travel_request'],{ queryParams: { id:  this.requestId} });
  }

  approve() {
    const commentsCtrl = this.approverForm.get('project_manager_comments');

    // Remove required validator
    commentsCtrl?.clearValidators();
    commentsCtrl?.updateValueAndValidity();

    const payload = {
      remarks: commentsCtrl?.value,
      level:'PM',
      action: 'APPROVE'
    };

    console.log('Approve Payload:', payload);
     this.travelService.approveOrRejectRequest(this.requestId,payload).subscribe(res=>{
       this.messageService.add({ severity: 'success', summary: '', detail: 'Request Approved' });
       setTimeout(() => {
          this.navigateToGrid()
        }, 1000);
    },(err: any) => { 
        this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  reject() {
    const commentsCtrl = this.approverForm.get('project_manager_comments');
    commentsCtrl?.setValidators([
      Validators.required,
      Validators.maxLength(100)
    ]);
    commentsCtrl?.updateValueAndValidity();
    if (this.approverForm.invalid) {
      commentsCtrl?.markAsTouched();
      return;
    }

    const payload = {
      remarks: commentsCtrl?.value,
      level: 'PM',
      action: 'REJECT'
    };

    console.log('Reject Payload:', payload);
    // call reject API here
    this.travelService.approveOrRejectRequest(this.requestId,payload).subscribe(res=>{
       this.messageService.add({ severity: 'success', summary: '', detail: 'Request Rejected' });
       setTimeout(() => {
          this.navigateToGrid()
        }, 1000);
    },(err: any) => { 
        this.activatedRouterService.updateError(err, this.messageService)
    })
  }


  getStatusClass(status: string): string {
    switch (status) {
      case 'CREATED':
        return 'badge bg-secondary';
      case 'APPROVED':
        return 'badge bg-success';
      case 'REJECTED':
        return 'badge bg-danger';
      default:
        return 'badge bg-light text-dark';
    }
  }

  getStatusIcon(status: string): string {
    switch (status) {
      case 'CREATED':
        return 'fa fa-file-text me-1';
      case 'APPROVED':
        return 'fa fa-check-circle me-1';
      case 'REJECTED':
        return 'fa fa-times-circle me-1';
      default:
        return '';
    }
  }
}
