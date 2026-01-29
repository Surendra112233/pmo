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
  selector: 'app-companies',
  templateUrl: './companies.component.html',
  styleUrls: ['./companies.component.scss'],
  imports: [TableModule, CommonModule, InputIconModule, IconFieldModule, ToastModule, DialogModule,
      ConfirmDialogModule, CheckboxModule, FormsModule, ReactiveFormsModule],
})
export class CompaniesComponent {
  @ViewChild('dt2') dt : Table | undefined
    companies:any[]=[];
    selectedCompany:any;
    displayDeleteDialog:boolean=false;
    constructor(
      private masterDataService:MasterDataService,
      private router:Router,    
      private messageService: MessageService,
      private activatedRouterService: ActivatedRouterService
    ) {}
  
    ngOnInit(){
      this.getCompanies()
    }
  
    getCompanies(){
      this.masterDataService.getAllCompanies().subscribe(res=>{
        this.companies=res['data']
        this.companies.sort((a, b) => {
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
      this.router.navigate(['/md/companies']);
    }
  
    addCompany() {
      this.router.navigate(['/md/add_company']);
    }
  
    viewCompany(company:any) {
      this.router.navigate(['/md/view_company'], { queryParams: {id:company.id} });
    }

    editCompany(company:any) {
      this.router.navigate(['/md/edit_company', company.id]);
    }
  
    deleteCompany(){
      this.masterDataService.deleteCompanyById(this.selectedCompany.id).subscribe(res=>{
        this.displayDeleteDialog = false;
        this.messageService.add({ severity: 'success', summary: '', detail: 'Company deleted successfully' });
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
      this.selectedCompany=company;
    }
  
    closeDeleteDialog() {
      this.displayDeleteDialog = false;
      this.selectedCompany=null;
    }

    getLocationNames() {
      // // Convert string -> array
      // if (this.company.location_name) {
      //   this.company.locationNames = this.company.location_name
      //     .split(',')
      //     .map((loc: string) => loc.trim()); // remove extra spaces
      // } else {
      //   this.company.locationNames = [];
      // }
    }
}
