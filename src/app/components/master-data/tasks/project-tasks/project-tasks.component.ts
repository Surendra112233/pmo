import { CommonModule } from '@angular/common';
import { Component, OnInit, ViewChild } from '@angular/core';
import { Table, TableModule } from 'primeng/table';
import { IconFieldModule } from 'primeng/iconfield';
import { InputIconModule } from 'primeng/inputicon';
import { Router } from '@angular/router';
import { ConfirmationService, MessageService } from 'primeng/api'
import { ToastModule } from 'primeng/toast';
import { DialogModule } from 'primeng/dialog';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { CheckboxModule } from 'primeng/checkbox';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRouterService } from '../../../../services/activated-router-service';
import { MasterDataService} from '../../../../services/master-data.service';
import { Tasks } from '../../../../models/tasks';
import * as XLSX from 'xlsx';

@Component({
    selector: 'app-project-tasks',
    imports: [TableModule, CommonModule, InputIconModule, IconFieldModule, ToastModule, DialogModule,
        ConfirmDialogModule, CheckboxModule, FormsModule, ReactiveFormsModule],
    templateUrl: './project-tasks.component.html',
    styleUrls: ['./project-tasks.component.scss'],
    providers: [ConfirmationService, MessageService],
    standalone:true
})
export class ProjectTasksComponent implements OnInit{
  @ViewChild('dt2') dt : Table | undefined
tasks:Tasks[]=[];
constructor(private router:Router,private masterDataService:MasterDataService,
  private activatedRouterService:ActivatedRouterService,private messageService:MessageService){}

  ngOnInit(): void {
    this.getProjectTask();
    
  }

  getProjectTask(){
  this.masterDataService.getTasks().subscribe(res=>{
    this.tasks=res['data'];
    this.tasks.sort((a, b) => b.task_code - a.task_code);
  },(err: any) => { 
    this.activatedRouterService.updateError(err, this.messageService)
  })
  }

  applyFilterGlobal($event:any, stringVal:any) {
    this.dt!.filterGlobal(($event.target as HTMLInputElement).value, stringVal);
  }
  navigateToGrid(){
    this.router.navigate(['/md/project_tasks']);
  }

  navigateToView(task_code:number){
    this.router.navigate(['/md/view_task'], { queryParams: { id: task_code} });    
  }

  addTask(){
    this.router.navigate(['/md/add_task']);
  }
  editTask(task_code:number){
    this.router.navigate(['/md/edit_task',task_code]);
  }

  deleteTask(task_code:number){
  this.masterDataService.deleteTask(task_code).subscribe(res=>{
      this.messageService.add({ severity: 'delete', summary: '', detail: 'Task Delete Successfully' });
      this.getProjectTask();
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  exportToExcel(): void {  
    // const worksheet: XLSX.WorkSheet = XLSX.utils.json_to_sheet(this.tasks);
    // const workbook: XLSX.WorkBook = { 
    //   Sheets: { 'tasks': worksheet },
    //   SheetNames: ['tasks']
    // };
    // const excelBuffer: any = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
    // this.saveExcelFile(excelBuffer, 'Project Tasks.xlsx');

    const worksheetData = [
      ['Task Code', 'Project Type', 'Phase' ,'Task Description'],
      ...this.tasks.map((item) => [          
        item.task_code,
        item.project_type,
        item.task_group,
        item.description
      ]),
    ];
  
    const worksheet: XLSX.WorkSheet = XLSX.utils.aoa_to_sheet(worksheetData);
    const workbook: XLSX.WorkBook = {
      Sheets: { 'tasks': worksheet },
      SheetNames: ['tasks']
    };
  
    const excelBuffer: any = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });  
    const filename = 'Project Tasks.xlsx';
    this.saveExcelFile(excelBuffer, filename);
  }

  // Function to save the Excel file
  private saveExcelFile(buffer: any, filename: string): void {
    const data: Blob = new Blob([buffer], { type: 'application/octet-stream' }); // Removed bookType
    const link = document.createElement('a');
    link.href = URL.createObjectURL(data);
    link.download = filename;
    link.click();
  }  
}
