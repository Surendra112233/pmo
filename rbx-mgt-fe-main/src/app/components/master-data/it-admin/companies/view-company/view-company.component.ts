import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { MessageService } from 'primeng/api';
import { ActivatedRouterService } from 'src/app/services/activated-router-service';
import { MasterDataService } from 'src/app/services/master-data.service';

@Component({
  standalone: true,
  selector: 'app-view-company',
  templateUrl: './view-company.component.html',
  styleUrls: ['./view-company.component.scss'],
  imports: [CommonModule]
})
export class ViewCompanyComponent {
 company: any;
 company_id:string = '';

  constructor(
    private router: Router,
    private masterDataService: MasterDataService,
    private activatedRouterService: ActivatedRouterService,
    private messageService: MessageService,
    private activatedRoute: ActivatedRoute
  ) {}

  ngOnInit(): void {
    this.activatedRoute.queryParams.subscribe((res) => {
      this.company_id = res['id'];
      if(this.company_id) {
        this.getCompanyById();
      }
    })
  }

  getCompanyById() {
    this.masterDataService.getCompanyById(this.company_id).subscribe((res: any) => {
      this.company = res['data'];    
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  onBack() {
    this.router.navigate(['/md/companies']);
  }

  onEdit() {
    this.router.navigate(['/md/edit_company', this.company_id]);
  }
}
