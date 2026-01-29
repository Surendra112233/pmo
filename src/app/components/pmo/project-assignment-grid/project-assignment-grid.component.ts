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
import { PMOService} from '../../../services/pmo.service';
import { ActivatedRouterService } from '../../../services/activated-router-service';
import { pmo } from '../../../models/pmo';
@Component({
    selector: 'app-project-assignment-grid',
    imports: [TableModule, CommonModule, InputIconModule, IconFieldModule, ToastModule, DialogModule,
        ConfirmDialogModule, CheckboxModule, FormsModule, ReactiveFormsModule],
    templateUrl: './project-assignment-grid.component.html',
    styleUrls: ['./project-assignment-grid.component.scss'],
    standalone:true
})
export class ProjectAssignmentGridComponent implements OnInit{
 @ViewChild('dt2') dt : Table | undefined
 projects:pmo[]=[];
 status = [
    {id:'all', name: 'All'},
    // {id:'open', name: 'Open'},
    {id:'active', name: 'Active'},
    // {id:'inactive', name: 'Inactive'},
    {id:'completed', name: 'Completed'},
  ];
 selectedStatus = 'active';
 filteredData:any = [];

  constructor(
    private router:Router,    
    private messageService: MessageService,
    private pmoService:PMOService,
     private activatedRouterService: ActivatedRouterService
  ) {}

  ngOnInit(): void {
    this.getProjects();
  }

  getProjects(){
    this.pmoService.getProjects().subscribe(res=>{
      this.projects=res['data'];
      this.projects = this.projects.sort((a:any, b:any) => {
        const dateA = new Date(a.updated_at || a.created_at).getTime();
        const dateB = new Date(b.updated_at || b.created_at).getTime();
        return dateB - dateA; // Descending order
      });
      this.filterProjectsByStatus();
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  filterProjectsByStatus() {
    if (this.selectedStatus === 'all') {
      this.filteredData = [...this.projects];
    } else {
      this.filteredData = this.projects.filter(
        (project:any) => project.project_status.toLowerCase() === this.selectedStatus
      );
    }
  }

  applyFilterGlobal($event:any, stringVal:any) {
    this.dt!.filterGlobal(($event.target as HTMLInputElement).value, stringVal);
  }

  navigateToGrid() {
    this.router.navigate(['/pmo/project-assignment']);
  }

  navigateToAddProject() {
    this.router.navigate(['/pmo/add-project-assignment']);
  }

  navigateToView(project_code:string) {
    this.router.navigate(['/pmo/view-project-assignment'], { queryParams: { id:  project_code} });
  }

  // editProject(id:string){
  //   this.router.navigate(['/home/pmo/edit-project-assignment',id]);
  // }

  // deleteProject(id:string){
  //   this.pmoService.deletePMO(id).subscribe(res=>{
  //     this.messageService.add({ severity: 'delete', summary: '', detail: 'PMO Delete Successfully' });
  //     this.getProjects();
  //   },(err: any) => { 
  //     this.activatedRouterService.updateError(err, this.messageService)
  //   })
  // }
}
