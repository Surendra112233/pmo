import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormArray, FormBuilder, FormControl, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { MessageService } from 'primeng/api';
import { CalendarModule } from 'primeng/calendar';
import { DropdownModule } from 'primeng/dropdown';
import { TableModule } from 'primeng/table';
import { ToastModule } from 'primeng/toast';
import { Tasks } from 'src/app/models/tasks';
import { ActivatedRouterService } from 'src/app/services/activated-router-service';
import { EmployeeService } from 'src/app/services/employee.service';
import { LoginService } from 'src/app/services/login.service';
import { MasterDataService } from 'src/app/services/master-data.service';
import { TravelService } from 'src/app/services/travel.service';

@Component({
  selector: 'app-raise-travel-request',
  templateUrl: './raise-travel-request.component.html',
  styleUrls: ['./raise-travel-request.component.scss'],
  imports: [ToastModule, DropdownModule, ReactiveFormsModule, CalendarModule,
    TableModule, CommonModule, FormsModule],
  standalone: true
})
export class RaiseTravelRequestComponent {
  requestForm!: FormGroup;
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
  tasksModel: Tasks = new Tasks();
  task_code: string = '';
  buttonValue: string = 'Submit';
  taskHeaderText = 'Add Task';
  employeeCode: any;
  role: any;
  today: Date = new Date();
  constructor(
    private loginService: LoginService,
    private formBuilder: FormBuilder,
    private router: Router,
    private messageService: MessageService, private activatedRoute: ActivatedRoute, private empService: EmployeeService,
    private activatedRouterService: ActivatedRouterService, private masterDataService: MasterDataService,
    private travelService: TravelService
  ) { }

  ngOnInit() {
    this.travelPurpose = [{ id: 1, purpose: 'Project' },
    { id: 2, purpose: 'Business Development' },
    { id: 3, purpose: 'Conference' },
    { id: 4, purpose: 'Training' },
    { id: 5, purpose: 'Meeting' },
    { id: 5, purpose: 'Others' }
    ]
    this.travelLocation = [{ id: 1, location: 'Domestic' }, { id: 2, location: 'International' }]
    this.travelModes = [
      { id: 1, mode: 'Flight', icon: 'fa-plane' },
      { id: 2, mode: 'Train', icon: 'fa-train' },
      { id: 3, mode: 'Road', icon: 'fa-car' }
    ];
    this.paymentsBy = [{ id: 1, payment: 'Company' }, { id: 2, payment: 'Client' }, { id: 3, payment: 'Self' }]
    this.idTypes = [{ id: 1, idType: 'Driving License' }, { id: 2, idType: 'National ID' }, { id: 3, idType: 'Aadhar' }, { id: 4, idType: 'PAN' }, { id: 5, idType: 'Others' }]
    this.acTypes = [{ id: 1, accommodation: 'Hotel' }, { id: 2, accommodation: 'Guest House' }]
    this.paymentDebitedTo = [{ id: 1, debitTo: 'Company' }, { id: 2, debitTo: 'Client' }]
    this.employeeCode = localStorage.getItem('userId');
    this.role = localStorage.getItem('roles');
    this.requestForm = this.formBuilder.group({
      employee_code: new FormControl('', [Validators.required]),
      employee_name: new FormControl('', [Validators.required]),
      department: new FormControl('', [Validators.required]),
      project_type: new FormControl('', [Validators.required]),
      project_code: new FormControl('', [Validators.required, Validators.minLength(3), Validators.maxLength(40)]),
      project_name: new FormControl('', [Validators.required, Validators.minLength(3), Validators.maxLength(40)]),
      country: new FormControl('', [Validators.required, Validators.minLength(3), Validators.maxLength(100)]),
      sbu_head: new FormControl('', [Validators.required]),
      delivery_manager: new FormControl('', [Validators.required]),
      project_manager: new FormControl('', [Validators.required]),
      travel_location: new FormControl('', [Validators.required]),
      travel_purpose: new FormControl('', [Validators.required]),
      others_specify: new FormControl(''),
      status: 'Submitted',
      travel_details: this.formBuilder.array([this.createTravelRow()]),
      travel_preferences: new FormControl('', [Validators.required]),
      accommodation_required: [false],  // yes/no or boolean
      accommodation: this.formBuilder.array([this.createAccommodationRow()]),
      date_of_birth: new FormControl('', [Validators.required]),
      age: new FormControl('', [Validators.required]),
      id_document_type: new FormControl('', [Validators.required]),
      id_document_number: new FormControl('', [Validators.required]),
      passport_number: new FormControl('', [Validators.required]),
      mobile: new FormControl('', [Validators.required]),
      alt_mobile: new FormControl('', [Validators.required]),
      email: new FormControl('', [Validators.required]),
      alt_email: new FormControl('', [Validators.required]),
      address: new FormControl('', [Validators.required]),
      comments: new FormControl(''),
    });
    this.handleTravelPurposeValidation();
    this.getDropdownData();
    this.getEmployeeDetails();
    this.getCountriesList()
    this.activatedRoute.paramMap.subscribe(params => {
      this.task_code = params.get('id') || '';
      if (this.task_code) {
        this.getTasksById();
        this.buttonValue = 'Update';
        this.taskHeaderText = 'Edit Task';
      }
      else {
        this.buttonValue = 'Submit';
        this.taskHeaderText = 'Add Task';
      }
    });

    this.requestForm.get('date_of_birth')?.valueChanges.subscribe(dob => {
      if (dob) {
        this.calculateAge(dob);
      }
    });
  }

  handleTravelPurposeValidation() {
  const travelPurposeCtrl = this.requestForm.get('travel_purpose');
  const othersCtrl = this.requestForm.get('others_specify');

  travelPurposeCtrl?.valueChanges.subscribe(value => {
    if (value === 'Others') {
      othersCtrl?.setValidators([Validators.required]);
    } else {
      othersCtrl?.clearValidators();
      othersCtrl?.reset(); // optional: clear value when not Others
    }
    othersCtrl?.updateValueAndValidity();
  });
}

  get travelDetails(): FormArray {
    return this.requestForm.get('travel_details') as FormArray;
  }

  onDobChange(dob: Date) {
    this.calculateAge(dob);
  }

  calculateAge(dob: Date) {
    const today = new Date();

    let age = today.getFullYear() - dob.getFullYear();
    const monthDiff = today.getMonth() - dob.getMonth();

    if (
      monthDiff < 0 ||
      (monthDiff === 0 && today.getDate() < dob.getDate())
    ) {
      age--;
    }

    this.requestForm.get('age')?.setValue(age);
  }


  getEmployeeDetails() {
    this.masterDataService.getEmployeeById(this.employeeCode).subscribe(res => {
      this.requestForm.patchValue({
        employee_code: res['employee']?.employee_code,
        employee_name: res['employee']?.name,
        department: res['employee']?.department,
        mobile: res['employee']?.mobile,
        email: res['employee']?.email
      })
    }, (err: any) => {
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  getCountriesList() {
    this.empService.getCountriesList().subscribe(res => {
      this.countriesList = res?.['data']
    }, (err: any) => {
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  filterProjects() {
    this.masterDataService.getProjectDetails(this.requestForm.get('project_type')?.value).subscribe(res => {
      this.projectCodeList = res?.['data']
    }, (err: any) => {
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  filterProjectsByProjectCode() {
    const obj = this.projectCodeList.find((obj: any) => obj?.project_code == this.requestForm.get('project_code')?.value)
    this.requestForm.patchValue({
      project_name: obj.project_description,
      country: obj.project_country,
      project_manager: obj.manager,
      delivery_manager: obj.delivery_head,
      sbu_head: obj.sbu_head
    })
  }

  addTravelRow() {
    this.travelDetails.push(this.createTravelRow());
  }

  removeTravelRow(i: number) {
    if (this.travelDetails.length > 1) {
      this.travelDetails.removeAt(i);
    }
  }

  createTravelRow() {
    return this.formBuilder.group({
      // Departure
      departure_country: [''],
      departure_from: [''],
      departure_date: [''],
      departure_time: [''],

      // Arrival
      arrival_country: [''],
      arrival_to: [''],
      arrival_date: [''],
      arrival_time: [''],

      // Others
      mode: [''],
      payment_by: [''],
      remarks: ['']
    });
  }

  createAccommodationRow() {
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

  get accommodations(): FormArray {
    return this.requestForm.get('accommodation') as FormArray;
  }

  addAccommodationRow() {
    this.accommodations.push(this.createAccommodationRow());
  }

  removeAccommodationRow(index: number) {
    if (this.accommodations.length > 1) {
      this.accommodations.removeAt(index);
    }
  }

  getDropdownData() {
    this.loginService.getDropdownData().subscribe(data => {
      this.projectTypeList = data.Project_Types;
      this.phaseList = data.Phase_List;
      // this.billableList = data.Billable_List;     
    });
  }

  getFormControl(formControlName: string) {
    return this.requestForm.get(formControlName);
  }

  getTasksById() {
    this.masterDataService.getTasksById(+this.task_code).subscribe(res => {
      this.tasksModel = res['task'];
      //const taskDetails=this.tasks.find(task=>task.task_code==+this.task_code);
      this.requestForm.patchValue({
        project_type: this.tasksModel?.project_type,
        task_group: this.tasksModel?.task_group,
        description: this.tasksModel?.description,
        // billable: this.tasksModel?.billable
      })
    }, (err: any) => {
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  formatDate(date: Date | string): string {
    if (!date) return '';

    const d = new Date(date);
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();

    return `${day}-${month}-${year}`; // dd/mm/yyyy
  }

  buildRequestBody() {
  const formValue = this.requestForm.value;

  return {
    employee_code: formValue.employee_code,
    employee_name: formValue.employee_name,
    department: formValue.department,
    project_type: formValue.project_type,
    project_code: formValue.project_code,
    project_name: formValue.project_name,
    project_manager: formValue.project_manager,
    country: formValue.country,
   // request_raised_by: this.role,
    request_raised_by: 'Employee',
    delivery_manager: formValue.delivery_manager,
    sbu_head: formValue.sbu_head,
    travel_location: formValue.travel_location,
    travel_purpose: formValue.travel_purpose,
    others_specify: formValue.others_specify,
    travel_preferences: formValue.travel_preferences,
    accommodation_required: formValue.accommodation_required,
    status: formValue.status,
    travel_details: formValue.travel_details.map((td:any) => ({
      departure_country: td.departure_country,
      departure_from: td.departure_from,
      departure_date: this.formatDate(td.departure_date),
      departure_time: td.departure_time+":00",
      arrival_country: td.arrival_country,
      arrival_to: td.arrival_to,
      arrival_date: this.formatDate(td.arrival_date),
      arrival_time: td.arrival_time+":00",
      mode: td.mode,
      payment_by: td.payment_by
    })),
    accommodation: formValue.accommodation_required
      ? formValue.accommodation.map((ac: any) => ({
          accommodation_type: ac.accommodation_type,
          check_in: ac.check_in ? this.formatDate(ac.check_in) : '',
          check_out: ac.check_out ? this.formatDate(ac.check_out) : '',
          no_of_days: Number(ac.no_of_days),
          city: ac.city,
          payment_to: ac.payment_to,
          remarks: ac.remarks
        }))
      : [],
    personal_details: {
      date_of_birth: this.formatDate(formValue.date_of_birth),
      age: Number(formValue.age),
      id_document_type: formValue.id_document_type,
      id_document_number: formValue.id_document_number,
      passport_number: formValue.passport_number,
      mobile: formValue.mobile,
      alt_mobile: formValue.alt_mobile,
      email: formValue.email,
      alt_email: formValue.alt_email,
      address: formValue.address,
      comments: formValue.comments
    }
  };
}

  onSubmit() {
  if (this.requestForm.invalid) {
    this.requestForm.markAllAsTouched();
    return;
  }

  const payload = this.buildRequestBody();
  console.log(payload);

  this.travelService.raiseRequest(payload).subscribe(res => {
        this.messageService.add({ severity: 'success', summary: '', detail: 'Request Raised Successfully' });
        setTimeout(() => {
          this.navigateToGrid()
        }, 1000);
      }, (err: any) => {
        this.activatedRouterService.updateError(err, this.messageService)
  })
}

  navigateToGrid() {
    this.router.navigate(['/travel/travel-requests']);
  }

  back() {
    this.task_code ? this.router.navigate(['/md/view_task'], { queryParams: { id: this.task_code } }) : this.router.navigate(['/md/project_tasks']);
  }

  onCheckInChange(index: number) {
    const row = this.accommodations.at(index);
    const checkIn = row.get('check_in')?.value;
    const checkOut = row.get('check_out')?.value;

    if (checkIn && checkOut && checkOut < checkIn) {
      row.get('check_out')?.reset();
      row.get('no_of_days')?.reset();
      return;
    }

    this.calculateDays(index);
  }

  onCheckOutChange(index: number) {
    const row = this.accommodations.at(index);
    const checkIn = row.get('check_in')?.value;
    const checkOut = row.get('check_out')?.value;

    if (checkIn && checkOut && checkOut < checkIn) {
      row.get('check_out')?.reset();
      row.get('no_of_days')?.reset();
      return;
    }

    this.calculateDays(index);
  }

  calculateDays(index: number) {
    const row = this.accommodations.at(index);
    const checkIn = row.get('check_in')?.value;
    const checkOut = row.get('check_out')?.value;

    if (!checkIn || !checkOut) {
      row.get('no_of_days')?.reset();
      return;
    }

    const start = new Date(checkIn);
    const end = new Date(checkOut);

    const diffTime = end.getTime() - start.getTime();
    const days = diffTime / (1000 * 60 * 60 * 24) + 1; // inclusive

    row.get('no_of_days')?.setValue(days);
  }

  onDepartureChange(index: number) {
  this.validateTravelDateTime(index);
}

onArrivalChange(index: number) {
  this.validateTravelDateTime(index);
}

validateTravelDateTime(index: number) {
  const row = this.travelDetails.at(index);

  const depDate = row.get('departure_date')?.value;
  const depTime = row.get('departure_time')?.value;
  const arrDate = row.get('arrival_date')?.value;
  const arrTime = row.get('arrival_time')?.value;

  if (!depDate || !depTime || !arrDate || !arrTime) {
    return;
  }

  const departureDateTime = this.combineDateAndTime(depDate, depTime);
  const arrivalDateTime = this.combineDateAndTime(arrDate, arrTime);

  if (arrivalDateTime <= departureDateTime) {
    // Invalid → reset arrival fields
    row.get('arrival_date')?.reset();
    row.get('arrival_time')?.reset();
  }
}

combineDateAndTime(date: Date, time: string): Date {
  const [hours, minutes] = time.split(':').map(Number);
  const combined = new Date(date);
  combined.setHours(hours, minutes, 0, 0);
  return combined;
}

}
