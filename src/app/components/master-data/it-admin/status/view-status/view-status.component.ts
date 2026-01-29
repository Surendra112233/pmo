import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { MessageService } from 'primeng/api';
import { ActivatedRouterService } from 'src/app/services/activated-router-service';
import { MasterDataService } from 'src/app/services/master-data.service';

@Component({
  standalone: true,
  selector: 'app-view-status',
  templateUrl: './view-status.component.html',
  styleUrls: ['./view-status.component.scss'],
  imports: [CommonModule]
})
export class ViewStatusComponent {
  status: any;
  status_id: string = '';
  
  constructor(
    private router: Router,
    private masterDataService: MasterDataService,
    private activatedRouterService: ActivatedRouterService,
    private messageService: MessageService,
    private activatedRoute: ActivatedRoute
  ) {}

  ngOnInit(): void {
    this.activatedRoute.queryParams.subscribe((res) => {
      this.status_id = res['id'];
      if(this.status_id) {
        this.getStatusById();
      }
    })
  }

  getStatusById() {
    this.masterDataService.getStatusById(this.status_id).subscribe((res: any) => {
      this.status = res['data'];
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  onBack() {
    this.router.navigate(['/md/status']);
  }

  onEdit() {
    this.router.navigate(['/md/edit_status', this.status_id]);
  }
}
