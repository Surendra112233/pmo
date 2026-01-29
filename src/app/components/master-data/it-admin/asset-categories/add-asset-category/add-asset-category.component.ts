import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormArray, FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { MessageService } from 'primeng/api';
import { DropdownModule } from 'primeng/dropdown';
import { ActivatedRouterService } from 'src/app/services/activated-router-service';
import { MasterDataService } from 'src/app/services/master-data.service';

@Component({
  standalone: true,
  selector: 'app-add-asset-category',
  templateUrl: './add-asset-category.component.html',
  styleUrls: ['./add-asset-category.component.scss'],
  imports: [ReactiveFormsModule, CommonModule, DropdownModule]
})
export class AddAssetCategoryComponent {
  categoryForm!: FormGroup;
  category_id:string = '';
  btn_text:string = '';
  page_title:string = '';

  assetTypes = [
    { label: 'HW', value: 'Hardware' },
    { label: 'SW', value: 'Software' }
  ];

  constructor(private fb: FormBuilder,
              private router: Router,
              private activatedRoute: ActivatedRoute,
              private masterDataService: MasterDataService,
              private messageService: MessageService,
              private activatedRouterService: ActivatedRouterService
  ) {}

  ngOnInit() {
    this.buildCategoryForm();

    this.activatedRoute.paramMap.subscribe(params => {
      this.category_id = params.get('id') || '';
      if(this.category_id){
        this.getCategoryDetails();
        this.btn_text='Update';
        this.page_title='Edit';
      } else{
       this.btn_text='Save';
       this.page_title='Add';
      }
    });
  }
  
  buildCategoryForm() {
    this.categoryForm = this.fb.group({
      asset_type: ['', Validators.required],
      asset_category: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(40)]],
      asset_sub_category: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(40)]]
    });
  }

  getCategoryDetails() {
    this.masterDataService.getAssetCategoryById(this.category_id).subscribe((res: any) => {
      let data = res['data'];

      // patch main fields
      this.categoryForm.patchValue({
        asset_type: data.asset_type,
        asset_category: data.asset_category,
        asset_sub_category: data.asset_sub_category
      });
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  onSubmit() {
    if (this.categoryForm.valid) {
      const formValue = { ...this.categoryForm.value };
      // console.log('Final payload:', formValue);

      if (this.category_id) {
        // call update API
        this.masterDataService.updateAssetCategory(this.category_id, formValue).subscribe( data => {
          this.messageService.add({ severity: 'success', summary: '', detail: 'Asset category updated successfully' });
          setTimeout(() => {
              this.router.navigate(['/md/asset_categories']);
          }, 1000);
        
        },(err: any) => {
          this.activatedRouterService.updateError(err, this.messageService);      
        });
      
      } else {
        // call create API
        this.masterDataService.addAssetCategory(formValue).subscribe( data => {
          this.messageService.add({ severity: 'success', summary: '', detail: 'Asset category added successfully' });
          setTimeout(() => {
              this.router.navigate(['/md/asset_categories']);
          }, 1000);
        
        },(err: any) => {
          this.activatedRouterService.updateError(err, this.messageService);      
        });
      }
    } else {
      this.categoryForm.markAllAsTouched();
    }
  }

  onCancel() {
    this.categoryForm.reset();
    this.router.navigate(['/md/asset_categories']);
  }
}
