import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { FormArray, FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { MessageService } from 'primeng/api';
import { DropdownModule } from 'primeng/dropdown';
import { AlphaNumericSpecialCharsDirective } from 'src/app/directives/alphanumeric.directive';
import { ActivatedRouterService } from 'src/app/services/activated-router-service';
import { MasterDataService } from 'src/app/services/master-data.service';

@Component({
  standalone: true,
  selector: 'app-add-asset-model',
  templateUrl: './add-asset-model.component.html',
  styleUrls: ['./add-asset-model.component.scss'],
  imports: [ReactiveFormsModule, CommonModule, DropdownModule, AlphaNumericSpecialCharsDirective]
})
export class AddAssetModelComponent {
  @Input() from_hardware: boolean = false; // default behavior
  @Input() from_software: boolean = false; // default behavior

  @Output() model_for_hardware = new EventEmitter<any>(); // for dialog usage
  @Output() model_for_software = new EventEmitter<any>(); // for dialog usage
  
  modelForm!: FormGroup;
  model_id:string = '';
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
    this.buildModelForm();

    this.activatedRoute.paramMap.subscribe(params => {
      this.model_id = params.get('id') || '';

      if(this.from_hardware || this.from_software) {
        this.btn_text='Save';
        this.page_title='Add';
      } else {
        if(this.model_id){
          this.getModelDetails();
          this.btn_text='Update';
          this.page_title='Edit';
        } else{
          this.btn_text='Save';
          this.page_title='Add';
        }
      }

    });
  }
  
  buildModelForm() {
    this.modelForm = this.fb.group({
      asset_model_code: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(15)]],
      asset_model_name: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(40)]]
    });
  }

  getModelDetails() {
    this.masterDataService.getAssetModelById(this.model_id).subscribe((res: any) => {
      let data = res['data'];

      // patch main fields
      this.modelForm.patchValue({
        asset_model_code: data.asset_model_code,
        asset_model_name: data.asset_model_name
      });
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  onSubmit() {
    if (this.modelForm.valid) {
      const formValue = { ...this.modelForm.value };
      console.log('Final payload:', formValue);

      if (this.model_id && !this.from_hardware && !this.from_software) {
        // call update API
        this.masterDataService.updateAssetModel(this.model_id, formValue).subscribe( data => {
          this.messageService.add({ severity: 'success', summary: '', detail: 'Asset model updated successfully' });
          setTimeout(() => {
              this.router.navigate(['/md/asset_models']);
          }, 1000);        
        },(err: any) => {
          this.activatedRouterService.updateError(err, this.messageService);      
        });

      } else {        
        // call create API
        this.masterDataService.addAssetModel(formValue).subscribe( data => {
          this.messageService.add({ severity: 'success', summary: '', detail: 'Asset model added successfully' });
          if(this.from_hardware) {
            this.model_for_hardware.emit(formValue); // emit newly added model to parent
          } else if(this.from_software) {
            this.model_for_software.emit(formValue);
          } else {
            setTimeout(() => {
              this.router.navigate(['/md/asset_models']);
            }, 1000);
          }
        
        },(err: any) => {
          this.activatedRouterService.updateError(err, this.messageService);      
        });                
      }
    } else {
      this.modelForm.markAllAsTouched();
    }
  }

  onCancel() {
    this.modelForm.reset();
    if(this.from_hardware) {
      this.model_for_hardware.emit(null);
    } else if(this.from_software) {
      this.model_for_software.emit(null);
    } else {
      this.router.navigate(['/md/asset_models']);
    } 
  }
}
