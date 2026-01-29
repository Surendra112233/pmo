import { CommonModule } from '@angular/common';
import { Component, OnInit, ViewEncapsulation } from '@angular/core';
import { FormGroup, FormControl, Validators, ReactiveFormsModule, FormBuilder, AbstractControl, ValidationErrors, FormArray } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ConfirmationService, MessageService } from 'primeng/api';
import { CalendarModule } from 'primeng/calendar';
import { DropdownModule } from 'primeng/dropdown';
import { ToastModule } from 'primeng/toast';
import { PMOService} from '../../../services/pmo.service';
import { pmo } from '../../../models/pmo';
import { ActivatedRouterService } from '../../../services/activated-router-service';
import { LoginService} from '../../../services/login.service';
import { MasterDataService} from '../../../services/master-data.service';
import { ProjectTeamComponent } from '../project-team/project-team.component';
import { NoSpaceDirective } from 'src/app/directives/no-space.directive';
import { AlphaNumericWithSpaceDirective } from 'src/app/directives/alphanumeric.directive';
import { NumbersOnlyDirective } from 'src/app/directives/numbers-only.directive';
import { AlphanumaricsWithSlashIphonDirective } from 'src/app/directives/alphanumarics-with-slash-iphon.directive';
import { AllowOnlyCharDirective } from 'src/app/directives/allow-only-char.directive';
import { DialogModule } from 'primeng/dialog';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { FirstLetterCapitalDirective } from 'src/app/directives/first-letter-capital.directive';

@Component({
    selector: 'app-add-project-assignment',
    imports: [ReactiveFormsModule, ToastModule, CalendarModule, CommonModule, DropdownModule,ProjectTeamComponent,
      NoSpaceDirective,NumbersOnlyDirective,AlphanumaricsWithSlashIphonDirective,
      AllowOnlyCharDirective, DialogModule, ConfirmDialogModule, FirstLetterCapitalDirective, AlphaNumericWithSpaceDirective],
    templateUrl: './add-project-assignment.component.html',
    styleUrls: ['./add-project-assignment.component.scss'],
    providers: [ConfirmationService, MessageService],
    standalone:true
})
export class AddProjectAssignmentComponent implements OnInit{
  projectForm!: FormGroup; 
  pmoModel:pmo=new pmo();
  project_code:string='';
  buttonValue:string='Submit'
  projectTypes:any[]=[];
  projectManagers: any[] = [];
  dhManagers: any[] = [];
  hrManagers: any[] = [];
  sbuHeads: any[] = [];
  clientNames: any[] = [];
  deliveryModel: any[] = [];
  statusList:any[]=[];
  regions:any[]=[];
  countriesByRegion:any[]=[];
  countries:any[]=[];
  projects:pmo=new pmo();
  projectCategory:any[]=[];
  projectHeaderText='Add Project';
  employeeDetails:any[]=[];
  isBudgetHrsLimit:boolean=false;
  isSubmitButton:boolean=false;
  enableProjectTeam:boolean = false;
  phaseList:any = [];
  allTasks:any = [];
  selectedPhases:any = [];
  editScreen:boolean = false;
  displayDeleteDialog:boolean=false;
  selectedPhaseRow:any;
  task_code:string = '';
  rowIndex:number=0;
  totalBudgetHours:number = 0;
  budgetHoursError:boolean = false;
  projectStartDate:any;
  projectEndDate:any;
  roles:any;
  isProjectsLoading:boolean = true;
  pmEmpId:any;
  delEmpId:any;
  sbuEmpId:any;
  constructor(private fb: FormBuilder,private router: Router,private pmoService:PMOService,private loginService:LoginService,
     private messageService: MessageService,
        private activatedRoute:ActivatedRoute,private masterDataService:MasterDataService,
         private activatedRouterService: ActivatedRouterService
  ) {}

  ngOnInit(): void {
    this.roles = localStorage.getItem('Roles');
    // this.buildForm();
    this.getDropdownData();
    this.getEmployeesForManagers();
    this.activatedRoute.paramMap.subscribe(params => {
      this.project_code = params.get('id') || '';
      if(this.project_code){
        this.buildEditForm();
        this.getProjectsById();
        this.buttonValue='Update';
        this.projectHeaderText='Edit Project';
        this.editScreen = true;
        // this.getPhases();
        this.getPhasesByProject();       
      } else{
       this.buildForm();
       this.buttonValue='Submit';
       this.projectHeaderText='Add Project';
      }
    });

    // this.projectForm.get('project_region')?.valueChanges.subscribe(() => {
    //   this.projectForm?.get('project_country')?.setValidators([Validators.required]);
    //   this.projectForm?.get('project_country')?.updateValueAndValidity();
    // });

    this.projectForm.get('inter_company')?.valueChanges.subscribe((isChecked: boolean) => {
      const contractingCompanyControl = this.projectForm.get('contracting_company');
      if (isChecked) {
        contractingCompanyControl?.setValidators([Validators.required]);
      } else {
        contractingCompanyControl?.clearValidators();
        this.projectForm.get('contracting_company')?.setValue('');
      }
      contractingCompanyControl?.updateValueAndValidity();
    });

    this.phaseWiseArray.valueChanges.subscribe(() => this.validatePhaseWiseTotalBudgetedHrs());

    this.projectForm.get('budgeted_hours')?.valueChanges.subscribe(() => {
      this.validateActualAllocatedHours();
    });
    
    this.projectForm.get('allocated_budgeted_percentage')?.valueChanges.subscribe(() => {
      this.validateActualAllocatedHours();
    });
  }
  getDropdownData(){
    this.loginService.getDropdownData().subscribe(data => {
      this.projectTypes=data.Project_Types;
      this.deliveryModel = data.Delivery_Model;
      this.statusList=data.Project_Status;
      this.regions=data.Regions;
      this.countriesByRegion=data.CountriesByRegion; 
      this.projectCategory=data.Project_Category;
    });
  }

  getPhases() {
    this.masterDataService.getTasks().subscribe((res:any) => {
      const project_type = this.projectForm.get('project_type')?.value;
      console.log("project_type:::", project_type);
      //get all phases added in master data
      this.allTasks = res?.data;
      this.onProjectTypeChange(project_type, 'onLoad');
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  onProjectTypeChange(selectedProjectType: any, actionType:string) {
    if(actionType == 'onLoad') {
      selectedProjectType = selectedProjectType;
    } else if(actionType == 'onChange') {
        // Clear existing phases and add a new empty phase
        const phaseWiseArray = this.projectForm.get('phaseWiseArray') as FormArray;
        phaseWiseArray?.clear();
        // console.log("sel ph:::", this.selectedPhases);
        if(this.projectForm.get('project_type')?.value == this.projects?.project_type ) {
          //if switched from selected project type to another project type and again switched to selected project type
          //example implementation --> integration --> implementation then again patch all the selected phases from response
          this.patchPhases();
        } else {
          phaseWiseArray?.push(this.createPhaseWiseGroup({ task: '', start_date:null, end_date:null, budgeted_hours: 0, allocated_hours: 0, worked_hours: 0 }));
        }
        selectedProjectType = selectedProjectType?.target.value;
    }

    // this.phaseList = []; // Clear existing values
    // const filteredTasks = this.allTasks.filter((task:any) => task.project_type === selectedProjectType);
    // this.phaseList = filteredTasks.map((task:any) => ({
    //   task_group: task.task_group,
    //   task_code: task.task_code
    // }));

    //sort all tasks so that phaseId-59 will be considered instead of phaseId-70 for Org Standard Tasks Phase.
    this.allTasks.sort((a:any, b:any) => a.task_code - b.task_code);
    const filteredTasks = this.allTasks.filter((task: any) => task.project_type === selectedProjectType);
    console.log("filteredTasks:::", filteredTasks);
    const uniqueTaskGroups = new Set();
    this.phaseList = []; // Clear existing values

    filteredTasks.forEach((task: any) => {
      if (!uniqueTaskGroups.has(task.task_group)) {
        uniqueTaskGroups.add(task.task_group);
        // if(task.task_group == "Organization Standard Tasks") {
        //   this.phaseList.push({
        //     task_group: task.task_group,
        //     task_code: 59 //changing 70 to 59
        //   });
        // } else {
        //   this.phaseList.push({
        //     task_group: task.task_group,
        //     task_code: task.task_code
        //   });
        // }
        this.phaseList.push({
          task_group: task.task_group,
          task_code: task.task_code
        });
      }
    });
  
    console.log("Updated phaseList:", this.phaseList);
  }

  getPhasesByProject() {
    this.pmoService.getPhasesByProject(this.project_code).subscribe((res:any) => {
      this.selectedPhases = res;
      // this.selectedPhases = this.selectedPhases.map((phase:any) => {
      //   if(phase.phase_name == "Organization Standard Tasks" && phase.project_code == "RBXint0001") {
      //     return {
      //       ...phase,
      //       task: 59 //changing 70 to 59
      //     }
      //   } else {
      //     return {
      //       ...phase
      //     }
      //   }
      // })
      this.patchPhases();
      this.enableProjectTeam = true;

    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })    
  }

  patchPhases() {
    const phaseArray = this.projectForm.get('phaseWiseArray') as FormArray;
    phaseArray.clear();
    this.selectedPhases.forEach((phase:any) => {
      phaseArray.push(this.createPhaseWiseGroup(phase));
    });
  }

  validatePhaseWiseTotalBudgetedHrs() {
    this.totalBudgetHours = this.phaseWiseArray.value.reduce((acc:any, phase:any) => acc + Number(phase.budgetHrs || 0), 0);
    const mainAmount = Number(this.projectForm.get('allocated_budgeted_hours')?.value || 0);
    console.log('Budget validation',this.totalBudgetHours,mainAmount)
    if(mainAmount!=0){
      this.budgetHoursError = this.totalBudgetHours > mainAmount;
    }
  }
  
  updateAllocatedHours(newAllocatedHours: number) {
    this.projectForm.get('allocated_hours')?.setValue(newAllocatedHours);
     const budgetedHours = this.projectForm.get('allocated_budgeted_hours')?.value;
    const allocatedHours = this.projectForm.get('allocated_hours')?.value;
    this.isBudgetHrsLimit=false;
    if (allocatedHours && budgetedHours && allocatedHours > budgetedHours) {
      this.isBudgetHrsLimit=true;
    }
  }

  getProjectsById(){
    this.pmoService.getProjectsById(this.project_code).subscribe(res=>{
     this.projects=res['data'];
     this.projectEndDate = new Date(this.projects?.to_date);
     this.projectStartDate = new Date(this.projects?.from_date);
     this.projectForm.patchValue({
      project_code: this.projects?.project_code,
      //project_name:this.projects?.project_name,
      project_category: this.projects?.project_category,
      project_type: this.projects?.project_type,
      project_description: this.projects?.project_description,
      project_country: this.projects?.project_country,
      project_manager: this.projects?.project_manager,
      delivery_head: this.projects?.delivery_head,
      contracting_company: this.projects?.contracting_company,
      hr: this.projects?.sbu_head,
      sbu_head :this.projects?.sbu_head,
      project_region: this.projects?.project_region,
      client_name: this.projects?.client_name,
      delivery_model: this.projects?.delivery_model,
      budgeted_hours: this.projects?.budgeted_hours,
      worked_hours: this.projects?.worked_hours,
      allocated_budgeted_percentage: this.projects?.allocated_budgeted_percentage,
      allocated_budgeted_hours: this.projects?.allocated_budgeted_hours,
      allocated_hours:  this.projects?.allocated_hours,
      notes: this.projects?.notes, 
      from_date: new Date(this.projects?.from_date),
      to_date: new Date(this.projects?.to_date),
       project_status: this.projects?.project_status //=='active' ?  'active' : 'inactive'
    });
    
    // check 'inter_company' if 'contracting_company' value exists
    const hasContractingCompany = !!this.projects?.contracting_company;
    console.log("hasContractingCompany::", hasContractingCompany)
    this.projectForm.patchValue({
      inter_company: hasContractingCompany
    });

    this.onRegionChange('onLoad');
    this.getPhases();
   },(err: any) => { 
     this.activatedRouterService.updateError(err, this.messageService)
   })
 }

 //here we are getting employees list for manager dropdown
 getEmployeesForManagers(){
  this.isProjectsLoading = true;
  this.masterDataService.getEmployeeDetails().subscribe(res=>{
     this.employeeDetails=res['data'];
     this.employeeDetails = this.employeeDetails.sort((a,b) => a.name.localeCompare(b.name));
    //  .filter((employee: any) => employee.status == 'active');
    //  this.projectManagers = this.employeeDetails.map((employee: any) => ({ name: employee.name }));

   this.projectManagers = this.employeeDetails
    .filter((employee: any) => Array.isArray(employee.roles) && employee.roles.includes('Manager') && employee.status == 'active')
    // .map((employee: any) => ({ name: employee.name }));
    .map((emp: { employee_code: any; name: any; }) => ({
        ...emp,
        employee_codewithName: `${emp.employee_code} - ${emp.name}`
      }));

    this.dhManagers = this.employeeDetails
    .filter((employee: any) => Array.isArray(employee.roles) && employee.roles.includes('DeliveryHead') && employee.status == 'active')
    //.map((employee: any) => ({ name: employee.name, employee_code: employee.employee_code }));
    .map((emp: { employee_code: any; name: any; }) => ({
        ...emp,
        employee_codewithName: `${emp.employee_code} - ${emp.name}`
      }));

    this.hrManagers = this.employeeDetails
    .filter((employee: any) => Array.isArray(employee.roles) && employee.roles.includes('HR') && employee.status == 'active')
    //.map((employee: any) => ({ name: employee.name, employee_code: employee.employee_code }));
    .map((emp: { employee_code: any; name: any; }) => ({
        ...emp,
        employee_codewithName: `${emp.employee_code} - ${emp.name}`
      }));

    this.sbuHeads = this.employeeDetails
    .filter((employee: any) => Array.isArray(employee.roles) && employee.roles.includes('SBUHead') && employee.status == 'active')
    //.map((employee: any) => ({ name: employee.name, employee_code: employee.employee_code }));
    .map((emp: { employee_code: any; name: any; }) => ({
        ...emp,
        employee_codewithName: `${emp.employee_code} - ${emp.name}`
      }));

   this.isProjectsLoading = false;
  },(err: any) => {
    this.isProjectsLoading = false; 
    this.activatedRouterService.updateError(err, this.messageService)
  })
}

  buildForm() {
    this.projectForm = this.fb.group({
      project_code: ["", [Validators.required, Validators.minLength(3), Validators.maxLength(10)]],
      project_description: ["", [Validators.required, Validators.minLength(3), Validators.maxLength(100)]],
      project_type: ["", [Validators.required]],
      project_category: ["", [Validators.required, Validators.maxLength(100)]],
      inter_company: [false],
      contracting_company: [''],
      project_status: ["", [Validators.required]],
      project_manager: ["", [Validators.required]],
      delivery_head: ["", [Validators.required]],
      hr: ["", [Validators.required]],
      from_date: ["", [Validators.required]],
      to_date: ["", [Validators.required]],
      client_name: ["", [Validators.required, Validators.minLength(3), Validators.maxLength(100)]],
      project_region: ["", [Validators.required]],
      project_country: ["", [Validators.required]],
      delivery_model: ["", [Validators.required]],
      budgeted_hours: [0, [Validators.required, Validators.min(0), Validators.maxLength(10)]],
      allocated_budgeted_percentage: [70, [Validators.required, Validators.min(70),  Validators.max(100), Validators.maxLength(3)]],
      allocated_budgeted_hours: [0, [Validators.required, Validators.min(0), Validators.maxLength(15)]],
      allocated_hours: [0, [Validators.min(0), Validators.maxLength(10)]],
      worked_hours: [0],
      notes: [""]
    }, { validators: [this.dateValidator, this.allocatedHoursValidator] });

    // // Add phaseWiseArray only if editScreen is true
    // if (this.editScreen == true) {
    //   this.projectForm.addControl('phaseWiseArray', this.fb.array([
    //     this.createPhaseWiseGroup({ task: '', budgeted_hours: 0, allocated_hours: 0, worked_hours: 0 })
    //   ]));
    // }
  }


  buildEditForm(){
    this.projectForm = this.fb.group({
      project_code: ["", [Validators.required,Validators.minLength(3),Validators.maxLength(10)]],
      //project_name:["",[Validators.required,Validators.minLength(3),Validators.maxLength(100)]],
      project_description: ["", [Validators.required,Validators.minLength(3),Validators.maxLength(100)]],
      project_type: ["", [Validators.required]],
      project_category: ["", [Validators.required,Validators.maxLength(100)]],
      inter_company: [false],
      contracting_company: [''],
      project_status: ["", [Validators.required]],
      project_manager: ["", [Validators.required]],
      delivery_head: ["", [Validators.required]],
      hr: ["", [Validators.required]],
      from_date: ["", [Validators.required]],
      to_date: ["", [Validators.required]],
      client_name: ["", [Validators.required,Validators.minLength(3),Validators.maxLength(100)]],
      project_region: ["", [Validators.required]],
      project_country: [""],
      delivery_model: ["", [Validators.required]],
      budgeted_hours: [0, [Validators.required, Validators.min(0),Validators.maxLength(10)]],
      allocated_budgeted_percentage: [0, [Validators.required, Validators.min(2), Validators.maxLength(3)]],
      allocated_budgeted_hours: [0, [Validators.required, Validators.min(0), Validators.maxLength(15)]],
      allocated_hours: [0, [Validators.min(0), Validators.maxLength(10)]],
      worked_hours: [0],
      notes: [""],
      phaseWiseArray: this.fb.array([this.createPhaseWiseGroup({ task: '', start_date:null, end_date:null, budgeted_hours: 0, allocated_hours: 0, worked_hours: 0 })])
    }, { validators:[this.dateValidator, this.allocatedHoursValidator]});
  }

  createPhaseWiseGroup(phase: any = {}): FormGroup {
    // helper to safely parse a date-like value, returning null if invalid/empty
    const safeDate = (val: any): Date | null => {
      if (val === null || val === undefined || val === '') return null;
      const d = new Date(val);
      return isNaN(d.getTime()) ? null : d;
    };

    const start = safeDate(phase.start_date);
    const end = safeDate(phase.end_date);

    return this.fb.group({
      phase: [phase.task || '', [Validators.required]],
      start_date: [start, [Validators.required]],
      end_date: [end, [Validators.required]],
      budgetHrs: [phase.budgeted_hours ?? 0, [Validators.required, Validators.min(0), Validators.maxLength(10), Validators.pattern(/^\d{1,10}$/)]],
      allocatedHrs: [phase.allocated_hours ?? 0, Validators.required],
      workedHrs: [phase.worked_hours ?? 0, Validators.required]
    });
  }

  // createPhaseWiseGroup(phase :any): FormGroup {
  //   console.log('patch phase:::', phase)
  // // createPhaseWiseGroup(phase = { phase: '', budgetHrs: 0, allocatedHrs: 0, workedHrs: 0 }): FormGroup {
  // return this.fb.group({
  //     phase: [phase.task || '', [Validators.required]],
  //     start_date: [new Date(phase.start_date)|| null, [Validators.required]],
  //     end_date: [new Date(phase.end_date) || null, [Validators.required]],
  //     // phase: [phase.task || '', [Validators.required, this.duplicatePhaseValidator.bind(this)]],
  //     budgetHrs: [phase.budgeted_hours || 0, [Validators.required, Validators.min(0), Validators.maxLength(10), Validators.pattern(/^\d{1,10}$/)]],
  //     allocatedHrs: [phase.allocated_hours || 0, Validators.required],
  //     workedHrs: [phase.worked_hours || 0, Validators.required]
  //   });
  // }

  // // Validator to prevent duplicate phases
  // duplicatePhaseValidator(control: AbstractControl) {
  //   const selectedPhases = this.phaseWiseArray.controls.map(ctrl => ctrl.value.phase);
  //   if (selectedPhases.filter(p => p === control.value).length > 1) {
  //     return { duplicate: true };
  //   }
  //   return null;
  // }

  // // Filter available phases (exclude already selected ones)
  // availablePhases() {
  //   return this.phaseList.filter((phase:any) =>
  //       !this.phaseWiseArray.controls.some(ctrl => ctrl.value.phase === phase.task_code)
  //   );
  // }

  get phaseWiseArray(): FormArray {
    return this.projectForm?.get('phaseWiseArray') as FormArray || this.fb.array([]);
  }

  addRate() {
    // this.phaseWiseArray.push(this.createPhaseWiseGroup());
    const phaseArray = this.projectForm.get('phaseWiseArray') as FormArray;
    phaseArray.push(this.createPhaseWiseGroup({ task: '', start_date:null, end_date:null, budgeted_hours: 0, allocated_hours: 0, worked_hours: 0 }));
  }

  removeRate(index: number) {
    // this.phaseWiseArray.removeAt(index);
    const phaseArray = this.projectForm.get('phaseWiseArray') as FormArray;
    phaseArray.removeAt(index);
  }

  getFormControl(formControlName:string) {
    return this.projectForm.get(formControlName);
  }

  getFormArrayControl(index: number, formControlName: string) {
    const activitiesArray = this.projectForm.get('phaseWiseArray') as FormArray;
    const rowGroup = activitiesArray.at(index) as FormGroup;
    return rowGroup.get(formControlName)
    // return (this.projectForm.get('phaseWiseArray') as FormArray).at(index).get(formControlName);
  }

  getFormValidation() {
    const controls = this.projectForm.controls;
    
    const isInterCompany = controls['inter_company'].value;
    const isContractingCompanyValid = isInterCompany ? !!controls['contracting_company'].value : true;

    const basicFieldsValid =  controls['project_code'].value &&
                              // controls['project_name'].value&&
                              controls['project_description'].value &&
                              controls['project_type'].value &&
                              controls['project_category'].value &&
                              controls['project_status'].value &&
                              controls['project_manager'].value &&
                              controls['delivery_head'].value &&
                              controls['hr'].value &&
                              controls['from_date'] &&
                              controls['to_date'] && 
                              controls['client_name'] &&
                              controls['project_region'] &&
                              controls['project_country'] &&
                              controls['delivery_model'] &&
                              controls['budgeted_hours'] &&
                              controls['allocated_budgeted_percentage'] &&
                              controls['allocated_budgeted_hours'] &&
                              controls['allocated_hours'] &&                              
                              controls['worked_hours'] &&
                              controls['notes'] &&
                              isContractingCompanyValid;                         
    return basicFieldsValid;
  }

  onRegionChange(type:string) {
    if(type=='onLoad') {
      //do nothing
    } else if(type=='onChange') {
      this.projectForm.get('project_country')?.setValue([]);
    }
    const selectedRegion=this.projectForm.get('project_region')?.value;
    // Update the countries based on the selected region
    if (selectedRegion && this.countriesByRegion[selectedRegion]) {
      this.countries = this.countriesByRegion[selectedRegion]; // Populate countries based on region
      console.log("this.countries:::", this.countries);
      
      this.projectForm?.get('project_country')?.addValidators(Validators.required);
      this.projectForm?.get('project_country')?.updateValueAndValidity();
      
    } else {
      this.countries = [];       // Clear countries if no region is selected

      this.projectForm?.get('project_country')?.clearValidators();
      this.projectForm?.get('project_country')?.updateValueAndValidity();
    }
  }
  
  navigateToGrid() {
    this.router.navigate(['/pmo/project-assignment']);
  }
  changeFormat(dateToTransfer:string){
    const date = new Date(dateToTransfer);
    const formattedDate = date.getFullYear() + '-' +
      String(date.getMonth() + 1).padStart(2, '0') + '-' +
      String(date.getDate()).padStart(2, '0');
    return formattedDate
  }

  dateValidator(control: AbstractControl): ValidationErrors | null {
    const startDate = control.get('from_date')?.value;
    const endDate = control.get('to_date')?.value;

    if (startDate && endDate && endDate <= startDate) {
      return { endDateLessThanStartDate: true };
    }

    return null;
  }

  // Validator to ensure allocated hours don't exceed budgeted hours
  allocatedHoursValidator(form: FormGroup): ValidationErrors | null {
    const budgetedHours = form.get('allocated_budgeted_hours')?.value;
    const allocatedHours = form.get('allocated_hours')?.value;

    if (allocatedHours && budgetedHours && allocatedHours > budgetedHours) {
      return { allocatedGreaterThanBudgeted: true };
    }

    return null;
  }
    

  selectedManager(event:any){
    console.log('project_manager:',event)
    this.pmEmpId = event.value.employee_code
  }

  selectedDelManager(event:any){
    console.log('del_manager:',event)
    this.delEmpId = event.value.employee_code
  }

  selectedSbuManager(event:any){
    console.log('del_manager:',event)
    this.sbuEmpId = event.value.employee_code
  }
  onSubmit(){
    this.messageService.clear(); 
    const formData = this.projectForm.value;
    console.log('formData',formData)
    Object.assign(this.pmoModel, formData);
    console.log('pmoModel',this.pmoModel)
    const payload = {
      project_code:this.pmoModel.project_code,
      from_date:this.changeFormat(this.pmoModel.from_date),
      to_date:this.changeFormat( this.pmoModel.to_date),
      project_status:this.pmoModel.project_status.toLowerCase(),
      project_description:this.pmoModel.project_description,
      project_type:this.pmoModel.project_type,
      project_category:this.pmoModel.project_category,
      project_manager:this.pmoModel.project_manager,
      delivery_head:this.pmoModel.delivery_head,
      contracting_company:this.pmoModel.contracting_company,
      // hr:this.pmoModel.hr,
      sbu_head:this.pmoModel.hr,
      client_name:this.pmoModel.client_name,
      project_region:this.pmoModel.project_region,
      project_country:this.pmoModel.project_country,
      delivery_model:this.pmoModel.delivery_model,
      budgeted_hours:this.pmoModel.budgeted_hours,
      allocated_budgeted_percentage:this.pmoModel.allocated_budgeted_percentage,
      allocated_budgeted_hours:this.pmoModel.allocated_budgeted_hours,
      allocated_hours:this.pmoModel.allocated_hours,
      worked_hours:this.pmoModel.worked_hours,
      notes:this.pmoModel.notes
    }
      
    // this.pmoModel.from_date=this.changeFormat(this.pmoModel.from_date);
    // this.pmoModel.to_date=this.changeFormat( this.pmoModel.to_date);
    // this.pmoModel.project_status=this.pmoModel.project_status.toLowerCase();
    // this.pmoModel.project_description=this.pmoModel.project_description
    // this.pmoModel.project_type=this.pmoModel.project_type
    // this.pmoModel.project_category=this.pmoModel.project_category
    // this.pmoModel.project_manager=this.pmoModel.project_manager
    // this.pmoModel.client_name=this.pmoModel.client_name
    // this.pmoModel.project_region=this.pmoModel.project_region
    // this.pmoModel.project_country=this.pmoModel.project_country
    // this.pmoModel.delivery_model=this.pmoModel.delivery_model
    // this.pmoModel.budgeted_hours=this.pmoModel.budgeted_hours
    // this.pmoModel.allocated_hours=this.pmoModel.allocated_hours
    // this.pmoModel.worked_hours=this.pmoModel.worked_hours
    // this.pmoModel.notes=this.pmoModel.notes

    if(this.project_code){
      this.pmoModel.project_code=this.project_code;
      this.pmoService.updatePMO(this.project_code,payload).subscribe(res=>{
        
        let phasePayloadArray = this.projectForm.get('phaseWiseArray')?.value;
        let allPhasesArray = JSON.stringify(phasePayloadArray);

        console.log("phasePayloadArray:::", phasePayloadArray);
        console.log("this.selectedPhases:::", this.selectedPhases);
        if(this.selectedPhases.length > 0) { //if updating exisitng phases 

          if(phasePayloadArray.length > this.selectedPhases.length) { //if any new phase is added in addition to existing phase
            //trigger add api
            const newRecords = phasePayloadArray.filter(
              (phase:any) => !this.selectedPhases.some((selected:any) => selected.task === phase.phase)
            );
            phasePayloadArray = newRecords;

            const addPhasePayload = phasePayloadArray.map((value: any) => ({
              task: value.phase,
              budgeted_hours: Number(value.budgetHrs),
              project_code: this.project_code,
              start_date: this.changeFormat(value.start_date),
              end_date: this.changeFormat(value.end_date)
            }))
            console.log("addPhasePayload with id:::", addPhasePayload);           


            // this.pmoService.createAndUpdatePhase(addPhasePayload).subscribe(res=> {
            this.pmoService.addPhase(addPhasePayload).subscribe((res:any)=> { //create newly added phase in addition to exisitng phase and then update
              phasePayloadArray = JSON.parse(allPhasesArray);
              console.log("phasePayloadArray without id:::", phasePayloadArray);
              console.log(res?.['data'])

              // phasePayloadArray with id
              phasePayloadArray = phasePayloadArray.map((phase:any) => {
                const matchingPhase = this.selectedPhases.find((sp:any) => sp.task === phase.phase);
                return {
                    ...phase,
                    id: matchingPhase ? matchingPhase.id : null  // Add id if match found
                };
              });

              const newlyAddedPhases = res?.data;
              // set id from response to matching phase in phasePayloadArray
              phasePayloadArray = phasePayloadArray.map((phase:any) => {
                const matchingPhase = newlyAddedPhases.find((np:any) => np.task === phase.phase);
                return {
                    ...phase,
                    id: phase.id !== null ? phase.id : matchingPhase ? matchingPhase.id : null  // Only update if id was null
                };
              });


              console.log("phasePayloadArray with id:::", phasePayloadArray);
              const updatePhasePayload = phasePayloadArray.map((value: any) => ({
                id: value.id,
                task: value.phase,
                budgeted_hours: Number(value.budgetHrs),
                project_code: this.project_code,
                start_date: this.changeFormat(value.start_date),
                end_date: this.changeFormat(value.end_date)
              }))
              
              
              this.pmoService.updatePhase(updatePhasePayload).subscribe(res=> {
                this.messageService.add({ severity: 'success', summary: '', detail: 'Project Updated Successfully' });
                setTimeout(() => {
                  const currentRoute = this.router.url;
                  this.router.navigateByUrl('/', { skipLocationChange: true }).then(() => {
                    this.router.navigateByUrl(currentRoute);
                    this.enableProjectTeam = true;
                  });
                }, 3000)
              }, (err:any) => {
                const errMsg = err?.error?.errors?.[0]?.error  || err?.error?.error;                
                // setTimeout(() => {
                  this.messageService.add({ severity: 'error', summary: '', detail: errMsg });
                // }, 500) 
                setTimeout(() => {
                  const currentRoute = this.router.url;
                  this.router.navigateByUrl('/', { skipLocationChange: true }).then(() => {
                    this.router.navigateByUrl(currentRoute);
                  });
                }, 3000)
              });
            }, (err:any) => {
              const errMsg = err?.error?.errors?.[0]?.error  || err?.error?.error;
              // setTimeout(() => {
                  this.messageService.add({ severity: 'error', summary: '', detail: errMsg });
              // }, 500) 
              setTimeout(() => {
                const currentRoute = this.router.url;
                this.router.navigateByUrl('/', { skipLocationChange: true }).then(() => {
                  this.router.navigateByUrl(currentRoute);
                });
              }, 3000)
            });
          } else { // if existing phases are updated without adding any new phase

            // phasePayloadArray.forEach((payload:any) => {
            //   const matchedPhase = this.selectedPhases.find((sp:any) => sp.task === payload.phase);
            
            //    //if exisitng phase is changed to another phase without adding any new phase then trigger add api or trigger update api
            //   if (matchedPhase && matchedPhase.id !== null) {
                //trigger update api

                // phasePayloadArray with id
                // phasePayloadArray = phasePayloadArray.map((phase:any) => {
                //   const matchingPhase = this.selectedPhases.find((sp:any) => sp.task === phase.phase);
                //   return {
                //       ...phase,
                //       id: matchingPhase ? matchingPhase.id : null  // Add id if match found
                //   };
                // });

                const usedIds = new Set();
                phasePayloadArray = phasePayloadArray.map((phase: any) => {
                  const matchingPhase = this.selectedPhases.find((sp: any) => sp.task === phase.phase);

                  if (matchingPhase) {
                    usedIds.add(matchingPhase.id);
                    return {
                      ...phase,
                      id: matchingPhase.id
                    };
                  } else {
                    // Find the first unused ID from selectedPhases
                    const remainingPhase = this.selectedPhases.find((sp: any) => !usedIds.has(sp.id));
                    if (remainingPhase) {
                      usedIds.add(remainingPhase.id);
                      return {
                        ...phase,
                        id: remainingPhase.id
                      };
                    } else {
                      // If no IDs left to assign, fallback to null
                      return {
                        ...phase,
                        id: null
                      };
                    }
                  }
                });
                console.log("phasePayloadArray with id:::", phasePayloadArray);
                console.log("this.selectedPhases:::", this.selectedPhases);
                const updatePhasePayload = phasePayloadArray.map((value: any) => ({
                  id: value.id,
                  task: value.phase,
                  budgeted_hours: Number(value.budgetHrs),
                  project_code: this.project_code,
                  start_date: this.changeFormat(value.start_date),
                  end_date: this.changeFormat(value.end_date)
                }))

                this.pmoService.updatePhase(updatePhasePayload).subscribe(res=> {
                  this.messageService.add({ severity: 'success', summary: '', detail: 'Project Updated Successfully' });

                  setTimeout(() => {
                    // this.navigateToGrid();                
                    const currentRoute = this.router.url;
                      this.router.navigateByUrl('/', { skipLocationChange: true }).then(() => {
                        this.router.navigateByUrl(currentRoute);
                    });
                  }, 3000);
                }, (err:any) => {
                  // console.log("err:::::::", err);
                  let errMsg = err?.error?.errors?.[0]?.error || err?.error?.error;
                  if(errMsg == "Phase Allocation with id 'None' not found.") {
                    errMsg = "Phase once created cannot be changed."
                  }
                  // setTimeout(() => {
                    this.messageService.add({ severity: 'error', summary: '', detail: errMsg });
                  // }, 500) 
                  setTimeout(() => {
                    const currentRoute = this.router.url;
                    this.router.navigateByUrl('/', { skipLocationChange: true }).then(() => {
                      this.router.navigateByUrl(currentRoute);
                    });
                  }, 3000)
                })
            //   } else {
            //     this.messageService.add({ severity: 'error', summary: '', detail: "Phase once created cannot be changed" });
            //     // //trigger add API
            //     // const addPhasePayload = phasePayloadArray.map((value: any) => ({
            //     //   task: value.phase,
            //     //   budgeted_hours: Number(value.budgetHrs),
            //     //   project_code: this.project_code
            //     // }))
      
            //     // this.pmoService.addPhase(addPhasePayload).subscribe(res=> {
            //     //   this.messageService.add({ severity: 'success', summary: '', detail: 'Project Updated Successfully' });
            //     //   setTimeout(() => {
            //     //     const currentRoute = this.router.url;
            //     //     this.router.navigateByUrl('/', { skipLocationChange: true }).then(() => {
            //     //       this.router.navigateByUrl(currentRoute);
            //     //       this.enableProjectTeam = true;
            //     //     });
            //     //   }, 500)
            //     // },(err: any) => { 
            //     //   this.activatedRouterService.updateError(err, this.messageService)
            //     // })
            //   }
            // });
          }
          
        } else { //if phase is added for first time
          //trigger add api
          const addPhasePayload = phasePayloadArray.map((value: any) => ({
            task: value.phase,
            budgeted_hours: Number(value.budgetHrs),
            project_code: this.project_code,
            start_date: this.changeFormat(value.start_date),
            end_date: this.changeFormat(value.end_date)
          }))

          // this.pmoService.createAndUpdatePhase(addPhasePayload).subscribe(res=> {
          this.pmoService.addPhase(addPhasePayload).subscribe(res=> {
            this.messageService.add({ severity: 'success', summary: '', detail: 'Project Updated Successfully' });
            setTimeout(() => {
              const currentRoute = this.router.url;
              this.router.navigateByUrl('/', { skipLocationChange: true }).then(() => {
                this.router.navigateByUrl(currentRoute);
                this.enableProjectTeam = true;
              });
            }, 3000)
          })
        }      
      },(err: any) => { 
        this.activatedRouterService.updateError(err, this.messageService)
      })
    }
    else{
      // this.pmoService.createProjectAssignment(this.pmoModel).subscribe(
      this.pmoService.createProjectAssignment(payload).subscribe(
        data=>{
        this.messageService.add({ severity: 'success', summary: '', detail: 'Project Created Successfully' });
        setTimeout(() => {
          this.navigateToGrid()
        }, 1000);
      },(err: any) => { 
        this.activatedRouterService.updateError(err, this.messageService)
      })
   
  }
}

validateActualAllocatedHours(): void {
  const budgetedHoursCtrl = this.projectForm.get('budgeted_hours');
  const percentageCtrl = this.projectForm.get('allocated_budgeted_percentage');
  const allocatedHoursCtrl = this.projectForm.get('allocated_budgeted_hours');

  const budgetedHours = +budgetedHoursCtrl?.value || 0;
  const allocatedPercentage = +percentageCtrl?.value || 0;

  // Only update if both fields are valid and percentage is within range
  if (budgetedHours >= 0 && allocatedPercentage >= 70 && allocatedPercentage <= 100) {
    const allocatedHours = (budgetedHours * allocatedPercentage) / 100;
    allocatedHoursCtrl?.setValue(allocatedHours);
    // allocatedHoursCtrl?.setValue(allocatedHours.toFixed(2));
  } else {
    allocatedHoursCtrl?.setValue(0);
  }
}

buildPMOModel(){
  const formData=this.projectForm.value;  
  this.pmoModel.project_code=formData.project_code;
  this.pmoModel.from_date=this.changeFormat(this.pmoModel.from_date);
  this.pmoModel.to_date=this.changeFormat( this.pmoModel.to_date);
  this.pmoModel.project_status=this.pmoModel.project_status.toLowerCase();
}

back(){
  this.project_code ? this.router.navigate(['/pmo/view-project-assignment'], { queryParams: { id:  this.project_code} }):this.router.navigate(['/pmo/project-assignment']);
 }

 testEnddate(end_date:any,start_date:any, type:string){
  // if(start_date.value>end_date.value){console.log("in");
  //   this.messageService.add({ severity: 'error', summary: 'Date validation Error', detail: 'End date must be greater than start date.' });
  // }

  if (start_date.value && end_date.value && start_date.value > end_date.value) {
    if(type == 'project') {
      this.messageService.add({
        severity: 'error',
        summary: 'Project End Date Validation Error',
        detail: 'Project end date must be greater than or equal to project start date.'
      });
    } else if (type == 'phase') {
        this.messageService.add({
          severity: 'error',
          summary: 'Phase End Date Validation Error',
          detail: 'Phase end date must be greater than or equal to phase start date.'
      });
    }
  }
}

submitButtonHide(event:boolean){
   this.isSubmitButton=event;
}


showDeleteDialog(phase:any,rowIndex:number){
  this.displayDeleteDialog = true;
  this.selectedPhaseRow=phase;
  this.rowIndex=rowIndex;
}
closeDeleteDialog() {
  this.displayDeleteDialog = false;
  this.selectedPhaseRow=null;
  this.rowIndex=0;
}
deleteProjectTeam(){
  this.task_code = this.selectedPhaseRow.value.phase;
  const selectedPhase = this.selectedPhases.find((phase:any) => phase.task === this.task_code);

  if(selectedPhase){
    this.pmoService.deletePhase(selectedPhase.id).subscribe(data=>{
      this.messageService.add({ severity: 'success', summary: '', detail: ' Deleted Successfully' });
      this.selectedPhases.splice(this.rowIndex,1);
      this.displayDeleteDialog = false;
     setTimeout(() => {
        const currentRoute = this.router.url;
        this.router.navigateByUrl('/', { skipLocationChange: true }).then(() => {
          this.router.navigateByUrl(currentRoute);
        });
     }, 1000)
    },(err: any) => {
      this.displayDeleteDialog = false; 
      this.activatedRouterService.updateError(err, this.messageService);
    });
  } else {
    this.displayDeleteDialog = false;
    this.removeRate(this.rowIndex);
  }
}

}
