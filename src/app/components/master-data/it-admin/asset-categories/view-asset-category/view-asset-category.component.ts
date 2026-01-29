import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { MessageService } from 'primeng/api';
import { ActivatedRouterService } from 'src/app/services/activated-router-service';
import { MasterDataService } from 'src/app/services/master-data.service';

@Component({
  standalone: true,
  selector: 'app-view-asset-category',
  templateUrl: './view-asset-category.component.html',
  styleUrls: ['./view-asset-category.component.scss'],
  imports: [CommonModule]
})
export class ViewAssetCategoryComponent {
  category: any;
  category_id:string = '';

  constructor(
    private router: Router,
    private masterDataService: MasterDataService,
    private activatedRouterService: ActivatedRouterService,
    private messageService: MessageService,
    private activatedRoute: ActivatedRoute
  ) {}

  ngOnInit(): void {
    this.activatedRoute.queryParams.subscribe((res) => {
      this.category_id = res['id'];
      if(this.category_id) {
        this.getCategoryById();
      }
    })
  }

  getCategoryById() {
    this.masterDataService.getAssetCategoryById(this.category_id).subscribe((res: any) => {
      this.category = res['data'];
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  onBack() {
    this.router.navigate(['/md/asset_categories']);
  }

  onEdit() {
    this.router.navigate(['/md/edit_category', this.category_id]);
  }
}
