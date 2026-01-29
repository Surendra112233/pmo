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
import { Tasks } from '../../../../models/tasks';
@Component({
    selector: 'app-view-task',
    imports: [ToastModule, CommonModule, ReactiveFormsModule, CalendarModule, FormsModule, CheckboxModule, RadioButtonModule],
    templateUrl: './view-task.component.html',
    styleUrls: ['./view-task.component.scss'],
    providers: [MessageService],
    standalone:true
})
export class ViewTaskComponent implements OnInit{
  task_code:string='';
 // taskForm!: FormGroup;
  tasks:Tasks=new Tasks();
  constructor(
    private router:Router,
    private formBuilder:FormBuilder,
    private activatedRoute:ActivatedRoute,
    private masterDataService:MasterDataService,private messageService: MessageService,
        private activatedRouterService: ActivatedRouterService
  ) {}

  ngOnInit(){
    this.activatedRoute.queryParams.subscribe((res) => {
      this.task_code=res['id']
    })
    this.getTasksById()
  }

  getTasksById(){
    this.masterDataService.getTasksById(+this.task_code).subscribe(res=>{
      this.tasks=res['task'];
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }


  navigateToGrid() {
    this.router.navigate(['/md/project_tasks']);
  }

  navigateToEditTask() {    
    this.router.navigate(['/md/edit_task',+this.task_code]);
  }

}
