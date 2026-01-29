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
import { UserService } from '../../../../services/user.service';
import { ActivatedRouterService } from '../../../../services/activated-router-service';
import { MasterDataService } from 'src/app/services/master-data.service';

@Component({
  standalone: true,
  selector: 'app-asset-models',
  templateUrl: './asset-models.component.html',
  styleUrls: ['./asset-models.component.scss'],
  imports: [TableModule, CommonModule, InputIconModule, IconFieldModule, ToastModule, DialogModule,
      ConfirmDialogModule, CheckboxModule, FormsModule, ReactiveFormsModule],
})
export class AssetModelsComponent {
  @ViewChild('dt2') dt : Table | undefined
  assetModels:any[]=[];
  selectedModel:any;
  displayDeleteDialog:boolean=false;
  constructor(
    private masterDataService:MasterDataService,
    private router:Router,    
    private messageService: MessageService,
    private activatedRouterService: ActivatedRouterService
  ) {}

  ngOnInit(){
    this.getModels()
  }

  getModels(){
    this.masterDataService.getAllAssetModels().subscribe(res=>{
      this.assetModels=res['data']
      this.assetModels.sort((a, b) => {
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
    this.router.navigate(['/md/asset_models']);
  }

  addModel() {
    this.router.navigate(['/md/add_model']);
  }

  viewModel(model:any) {
    this.router.navigate(['/md/view_model'], { queryParams: {id: model.asset_model_id} });
  }

  editModel(model:any) {
    this.router.navigate(['/md/edit_model', model.asset_model_id]);
  }

  deleteModel(){
    this.masterDataService.deleteAssetModelById(this.selectedModel.asset_model_id).subscribe(res=>{
      this.displayDeleteDialog = false;
      this.messageService.add({ severity: 'success', summary: '', detail: 'Asset model deleted successfully' });
      setTimeout(() => {
        const currentRoute = this.router.url;
        this.router.navigateByUrl('/', { skipLocationChange: true }).then(() => {
          this.router.navigateByUrl(currentRoute);
        });
      }, 1000)
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })    
  }

  showDeleteDialog(company:any){
    this.displayDeleteDialog = true;
    this.selectedModel=company;
  }

  closeDeleteDialog() {
    this.displayDeleteDialog = false;
    this.selectedModel=null;
  }
}
