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
  selector: 'app-hardware-grid',
  templateUrl: './hardware-grid.component.html',
  styleUrls: ['./hardware-grid.component.scss'],
  imports: [TableModule, CommonModule, InputIconModule, IconFieldModule, ToastModule, DialogModule,
        ConfirmDialogModule, CheckboxModule, FormsModule, ReactiveFormsModule],
})
export class HardwareGridComponent {
  @ViewChild('dt2') dt : Table | undefined
  hardware:any[]=[];
  selectedCompany:any;
  displayDeleteDialog:boolean=false;
  constructor(
    private assetService:AssetManagementService,
    private router:Router,    
    private messageService: MessageService,
    private activatedRouterService: ActivatedRouterService
  ) {}

  ngOnInit(){
    this.getHardwares()
  }

  getHardwares(){
     this.assetService.getAllHardwares().subscribe(res=>{
      this.hardware=res['data'];
      this.hardware.sort((a, b) => {
        const dateA = new Date(a.updatedAt || a.createdAt).getTime();
        const dateB = new Date(b.updatedAt || b.createdAt).getTime();
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
    this.router.navigate(['/IT/hardware']);
  }

  addHardware() {
    this.router.navigate(['/IT/add_hardware']);
  }

  viewHardware(hardware:any) {
    this.router.navigate(['/IT/view_hardware'], { queryParams: {id:hardware.id} });
  }

  editHardware(hardware:any) {
    this.router.navigate(['/IT/edit_hardware', hardware.id]);
  }
}
