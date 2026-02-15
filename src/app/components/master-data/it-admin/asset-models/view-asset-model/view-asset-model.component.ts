import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { MessageService } from 'primeng/api';
import { ActivatedRouterService } from 'src/app/services/activated-router-service';
import { MasterDataService } from 'src/app/services/master-data.service';

@Component({
  standalone: true,
  selector: 'app-view-asset-model',
  templateUrl: './view-asset-model.component.html',
  styleUrls: ['./view-asset-model.component.scss'],
  imports: [CommonModule]
})
export class ViewAssetModelComponent {
  model: any;
  model_id:string = '';

  constructor(
    private router: Router,
    private masterDataService: MasterDataService,
    private activatedRouterService: ActivatedRouterService,
    private messageService: MessageService,
    private activatedRoute: ActivatedRoute
  ) {}

  ngOnInit(): void {
    this.activatedRoute.queryParams.subscribe((res) => {
      this.model_id = res['id'];
      if(this.model_id) {
        this.getModelById();
      }
    })
  }

  getModelById() {
    this.masterDataService.getAssetModelById(this.model_id).subscribe((res: any) => {
      this.model = res['data'];
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  onBack() {
    this.router.navigate(['/md/asset_models']);
  }

  onEdit() {
    this.router.navigate(['/md/edit_model', this.model_id]);
  }
}
