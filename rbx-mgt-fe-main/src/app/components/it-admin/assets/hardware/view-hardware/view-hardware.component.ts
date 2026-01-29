import { CommonModule, DatePipe } from '@angular/common';
import { Component } from '@angular/core';
import { FormArray, FormGroup } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { MessageService } from 'primeng/api';
import { TableModule } from 'primeng/table';
import { ActivatedRouterService } from 'src/app/services/activated-router-service';
import { AssetManagementService } from 'src/app/services/asset-management.service';
import { MasterDataService } from 'src/app/services/master-data.service';

@Component({
  standalone: true,
  selector: 'app-view-hardware',
  templateUrl: './view-hardware.component.html',
  styleUrls: ['./view-hardware.component.scss'],
  imports: [TableModule, DatePipe, CommonModule]
})
export class ViewHardwareComponent {
  hardwareForm!: FormGroup;
  assignmentDetails!: FormArray;
  hardwareDetails:any = {};
  showPassword = false;

  id:string = '';
  pdfUrl:string = '';
  imgFilePdfUrl: string = '';
  invFilePdfUrl: string = '';
  imgAvailable: boolean = false;
  invAvailable: boolean = false;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private assetService: AssetManagementService,
    private activatedRouterService: ActivatedRouterService,
    private messageService: MessageService
  ) {}

  ngOnInit(): void {
    this.route.queryParams.subscribe((res) => {
      this.id = res['id'];

      if (this.id) {
        this.assetService.getHardwareById(this.id).subscribe((res: any) => {
          this.hardwareDetails = res['data'] || [];
          // this.Assignment_Details = res['Assignment_Details'] || [];

          if(Object.entries(res['data']).length > 0) {
            this.imgFilePdfUrl=res['data']?.['image'];
            if(this.imgFilePdfUrl?.includes('null') || this.imgFilePdfUrl == undefined){
              this.imgAvailable=false;
            }
            else{
              this.imgAvailable=true;
            }

            this.invFilePdfUrl=res['data']?.['invoice_copy'];
            if(this.invFilePdfUrl?.includes('null')  || this.invFilePdfUrl == undefined){
              this.invAvailable=false;
            }
            else{
              this.invAvailable=true;
            }
          }
        });
      }
    })
  }

  togglePassword() {
    this.showPassword = !this.showPassword;
  }

  onBack() {
    this.router.navigate(['/IT/hardware']);
  }

  onEdit() {
    this.router.navigate(['/IT/edit_hardware', this.id]);
  }

  getMaskedPassword(password: string | null | undefined): string {
    if (!password) {
      return '-';
    }
    return '*'.repeat(password.length);
  }
  
  viewPdf(section: string) {
    const fileUrl = section === 'image' ? this.imgFilePdfUrl : this.invFilePdfUrl;

    if (!fileUrl) {
      this.messageService.add({
        severity: 'warn',
        summary: 'File not available',
        detail: 'No file found to display'
      });
      return;
    }

    // open a blank tab immediately to avoid popup blockers
    const popup = window.open('', '_blank');

    this.assetService.viewPdfFile(fileUrl).subscribe({
      next: (blob: Blob) => {
        // prefer backend provided mime-type
        const blobUrl = URL.createObjectURL(blob);
        if (popup) {
          popup.location.href = blobUrl;
        } else {
          window.open(blobUrl, '_blank');
        }
      },
      error: (err: any) => {
        if (popup) popup.close();
        this.activatedRouterService.updateError(err, this.messageService);
      }
    });
  }
}
