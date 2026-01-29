import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { MessageService } from 'primeng/api';
import { ActivatedRouterService } from 'src/app/services/activated-router-service';
import { MasterDataService } from 'src/app/services/master-data.service';

@Component({
  standalone: true,
  selector: 'app-view-supplier',
  templateUrl: './view-supplier.component.html',
  styleUrls: ['./view-supplier.component.scss'],
  imports: [CommonModule]
})
export class ViewSupplierComponent {
  supplier: any;
  supplier_id:string = '';

  constructor(
    private router: Router,
    private masterDataService: MasterDataService,
    private activatedRouterService: ActivatedRouterService,
    private messageService: MessageService,
    private activatedRoute: ActivatedRoute
  ) {}

  ngOnInit(): void {
    this.activatedRoute.queryParams.subscribe((res) => {
      this.supplier_id = res['id'];
      if(this.supplier_id) {
        this.getSupplierById();
      }
    })
  }

  getSupplierById() {
    this.masterDataService.getSupplierById(this.supplier_id).subscribe((res: any) => {
      this.supplier = res['data'];
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  onBack() {
    this.router.navigate(['/md/suppliers']);
  }

  onEdit() {
    this.router.navigate(['/md/edit_supplier', this.supplier_id]);
  }
}
