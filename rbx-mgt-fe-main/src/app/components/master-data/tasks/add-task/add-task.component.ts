import { CommonModule } from '@angular/common';
import { Component, signal } from '@angular/core';
import { FormBuilder, FormControl, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ConfirmationService, MessageService } from 'primeng/api';
import { CalendarModule } from 'primeng/calendar';
import { DropdownModule } from 'primeng/dropdown';
import { ToastModule } from 'primeng/toast';
import * as moment from 'moment-timezone';
import 'moment-timezone';
import { LoginService } from '../../../../services/login.service';
import { ActivatedRouterService } from '../../../../services/activated-router-service';
import { MasterDataService} from '../../../../services/master-data.service';
import { Tasks} from '../../../../models/tasks';
import { NoSpaceDirective } from 'src/app/directives/no-space.directive';
import { AlphaNumericSpecialCharsDirective } from 'src/app/directives/alphanumeric.directive';
import { FirstLetterCapitalDirective } from 'src/app/directives/first-letter-capital.directive';

@Component({
    selector: 'app-add-task',
    imports: [ReactiveFormsModule, ToastModule, CalendarModule, CommonModule, DropdownModule,
      NoSpaceDirective,AlphaNumericSpecialCharsDirective, FirstLetterCapitalDirective],
    templateUrl: './add-task.component.html',
    styleUrls: ['./add-task.component.scss'],
    providers: [ConfirmationService, MessageService],
    standalone:true
})
export class AddTaskComponent {
  projectForm!: FormGroup;
  projectTypeList:any=[];
  phaseList:any=[];
  // billableList:any=[];
  tasksModel:Tasks=new Tasks();
  task_code:string='';
  buttonValue:string='Submit';
  taskHeaderText='Add Task';
  constructor(
    private loginService:LoginService,
    private formBuilder: FormBuilder,
    private router: Router,
    private messageService: MessageService,private activatedRoute:ActivatedRoute,
     private activatedRouterService: ActivatedRouterService,private masterDataService:MasterDataService
  ) {}

  ngOnInit(){
    this.projectForm = this.formBuilder.group({
      project_type: new FormControl('', [Validators.required]),
      task_group: new FormControl('', [Validators.required,Validators.minLength(3),Validators.maxLength(40)]),
      description: new FormControl('', [Validators.required,Validators.minLength(3),Validators.maxLength(100)]),
      // billable: new FormControl('', [Validators.required]),
    });
    this.getDropdownData();
    this.activatedRoute.paramMap.subscribe(params => {
      this.task_code = params.get('id') || '';
      if(this.task_code){
        this.getTasksById();
        this.buttonValue='Update';
        this.taskHeaderText='Edit Task';
      }
      else{
       this.buttonValue='Submit';
       this.taskHeaderText='Add Task';
      }
    });
  }

  getDropdownData(){
    this.loginService.getDropdownData().subscribe(data => {
      this.projectTypeList=data.Project_Types;
      this.phaseList = data.Phase_List;
      // this.billableList = data.Billable_List;     
    });
  }

  getFormControl(formControlName:string) {
    return this.projectForm.get(formControlName);
  }

  getTasksById(){
    this.masterDataService.getTasksById(+this.task_code).subscribe(res=>{
      this.tasksModel=res['task'];
     //const taskDetails=this.tasks.find(task=>task.task_code==+this.task_code);
      this.projectForm.patchValue({
        project_type: this.tasksModel?.project_type,
        task_group: this.tasksModel?.task_group,
        description: this.tasksModel?.description,
        // billable: this.tasksModel?.billable
      })
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  onSubmit(){ 
    if(this.task_code){
    this.tasksModel.task_code=+this.task_code;
    this.tasksModel.task_group=this.projectForm.get('task_group')?.value;
    this.tasksModel.project_type=this.projectForm.get('project_type')?.value;
    this.tasksModel.description=this.projectForm.get('description')?.value;
    // this.tasksModel.billable=this.projectForm.get('billable')?.value;
      this.masterDataService.updateTask(+this.task_code,this.tasksModel).subscribe(res=>{
        this.messageService.add({ severity: 'success', summary: '', detail: 'Task Updated Successfully' });
        setTimeout(() => {
          this.navigateToGrid()
        }, 1000);
      },(err: any) => { 
        this.activatedRouterService.updateError(err, this.messageService)
      })
    }
else{
    this.masterDataService.addTask(this.projectForm.value).subscribe(res=>{
      this.messageService.add({ severity: 'success', summary: '', detail: 'Task added successfully' });
      setTimeout(() => {
        this.navigateToGrid()
      }, 1000);
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }
  }

  navigateToGrid(){
    this.router.navigate(['/md/project_tasks']);
  }

  back(){
   this.task_code ? this.router.navigate(['/md/view_task'],{ queryParams: { id: this.task_code} }):this.router.navigate(['/md/project_tasks']);
  }
}
