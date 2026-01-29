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
import { MasterDataService } from 'src/app/services/master-data.service';

@Component({
  standalone: true,
  selector: 'app-asset-categories',
  templateUrl: './asset-categories.component.html',
  styleUrls: ['./asset-categories.component.scss'],
  imports: [TableModule, CommonModule, InputIconModule, IconFieldModule, ToastModule, DialogModule,
      ConfirmDialogModule, CheckboxModule, FormsModule, ReactiveFormsModule],
})
export class AssetCategoriesComponent {
  @ViewChild('dt2') dt : Table | undefined
  assetCategories:any[]=[];
  selectedCategory:any;
  displayDeleteDialog:boolean=false;
  constructor(
    private masterDataService:MasterDataService,
    private router:Router,    
    private messageService: MessageService,
    private activatedRouterService: ActivatedRouterService
  ) {}

  ngOnInit(){
    this.getCategories()
  }

  getCategories(){
    this.masterDataService.getAllAssetCategories().subscribe(res=>{
      this.assetCategories=res['data']
      this.assetCategories.sort((a, b) => {
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
    this.router.navigate(['/md/asset_categories']);
  }

  addCategory() {
    this.router.navigate(['/md/add_category']);
  }

  viewCategory(category:any) {
    this.router.navigate(['/md/view_category'], { queryParams: {id: category.asset_id} });
  }

  editCategory(category:any) {
    this.router.navigate(['/md/edit_category', category.asset_id]);
  }

  deleteCategory(){
    this.masterDataService.deleteAssetCategoryById(this.selectedCategory.asset_id).subscribe(res=>{
      this.displayDeleteDialog = false;
      this.messageService.add({ severity: 'success', summary: '', detail: 'Asset category deleted successfully' });
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

  showDeleteDialog(category:any){
    this.displayDeleteDialog = true;
    this.selectedCategory=category;
  }

  closeDeleteDialog() {
    this.displayDeleteDialog = false;
    this.selectedCategory=null;
  }
}
