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
import { ActivatedRouterService } from '../../../../../services/activated-router-service';
import { AssetManagementService } from 'src/app/services/asset-management.service';

@Component({
  standalone: true,
  selector: 'app-software-grid',
  templateUrl: './software-grid.component.html',
  styleUrls: ['./software-grid.component.scss'],
  imports: [TableModule, CommonModule, InputIconModule, IconFieldModule, ToastModule, DialogModule,
        ConfirmDialogModule, CheckboxModule, FormsModule, ReactiveFormsModule],
})
export class SoftwareGridComponent {
  @ViewChild('dt2') dt : Table | undefined
  software:any[]=[];
  selectedCompany:any;
  displayDeleteDialog:boolean=false;
  constructor(
    private assetService:AssetManagementService,
    private router:Router,    
    private messageService: MessageService,
    private activatedRouterService: ActivatedRouterService
  ) {}

  ngOnInit(){
    this.getSoftwares()
  }

  getSoftwares(){
    this.assetService.getAllSoftwares().subscribe(res=>{
      this.software=res['data']
      this.software.sort((a, b) => {
        const dateA = new Date(a.updated_at || a.created_at).getTime();
        const dateB = new Date(b.updated_at || b.created_at).getTime();
        return dateB - dateA; // Descending order
      });
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  applyFilterGlobal($event:any, stringVal:any) {
    this.dt!.filterGlobal(($event.target as HTMLInputElement).value, stringVal);
  }

  navigateToGrid() {
    this.router.navigate(['/IT/software']);
  }

  addSoftware() {
    this.router.navigate(['/IT/add_software']);
  }

  viewSoftware(software:any) {
    this.router.navigate(['/IT/view_software'], { queryParams: {id:software.id} });
  }

  editSoftware(software:any) {
    this.router.navigate(['/IT/edit_software', software.id]);
  }
}
