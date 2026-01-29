import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { FormArray, FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { MessageService } from 'primeng/api';
import { DropdownModule } from 'primeng/dropdown';
import { AlphaNumericWithSpaceDirective } from 'src/app/directives/alphanumeric.directive';
import { ActivatedRouterService } from 'src/app/services/activated-router-service';
import { LoginService } from 'src/app/services/login.service';
import { MasterDataService } from 'src/app/services/master-data.service';

@Component({
  standalone: true,
  selector: 'app-add-supplier',
  templateUrl: './add-supplier.component.html',
  styleUrls: ['./add-supplier.component.scss'],
  imports: [ReactiveFormsModule, CommonModule, DropdownModule, AlphaNumericWithSpaceDirective]
})
export class AddSupplierComponent {
  @Input() from_hardware: boolean = false; // default behavior
  @Input() from_software: boolean = false; // default behavior

  @Output() supplier_for_hardware = new EventEmitter<any>(); // for dialog usage
  @Output() supplier_for_software = new EventEmitter<any>(); // for dialog usage

  supplierForm!: FormGroup;
  regions:any[]=[];
  countriesByRegion:any[]=[];
  countries:any[]=[];
  supplier_id:string = '';
  btn_text:string = '';
  page_title:string = '';

  constructor(private fb: FormBuilder,
              private loginService: LoginService,
              private router: Router,
              private activatedRoute: ActivatedRoute,
              private masterDataService: MasterDataService,
              private messageService: MessageService,
              private activatedRouterService: ActivatedRouterService
  ) {}

  ngOnInit() {
    this.buildSupplierForm();
    this.getDropDownData();

    this.activatedRoute.paramMap.subscribe(params => {
      this.supplier_id = params.get('id') || '';

      if(this.from_hardware || this.from_software) {
        this.btn_text='Save';
        this.page_title='Add';
      } else {
        if(this.supplier_id){
          this.getSupplierDetails();
          this.btn_text='Update';
          this.page_title='Edit';
        } else{
        this.btn_text='Save';
        this.page_title='Add';
        }
      }

    });
  }
  
  buildSupplierForm() {
    this.supplierForm = this.fb.group({
      supplier: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(40)]],
      address: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(80)]],
      country: ['', Validators.required],
      geo_region: ['', Validators.required]
    });
  }

  getDropDownData() {
    this.loginService.getDropdownData().subscribe(data => {     
      this.regions=data.Regions;
      this.countriesByRegion=data.CountriesByRegion;
    });
  }

  getSupplierDetails() {
    this.masterDataService.getSupplierById(this.supplier_id).subscribe((res: any) => {
      let data = res['data'];

      // patch main fields
      this.supplierForm.patchValue({
        supplier: data.supplier,
        address: data.address,
        country: data.country,
        geo_region: data.geo_region
      });
      this.onRegionChange('onLoad');
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  onRegionChange(type:string) {
    if(type=='onLoad') {
      //do nothing
    } else if(type=='onChange') {
      this.supplierForm.get('country')?.setValue([]);
    }
    const selectedRegion=this.supplierForm.get('geo_region')?.value;

    // Update the countries based on the selected region
    if (selectedRegion && this.countriesByRegion[selectedRegion]) {
      this.countries = this.countriesByRegion[selectedRegion]; // Populate countries based on region
      
      this.supplierForm?.get('country')?.addValidators(Validators.required);
      this.supplierForm?.get('country')?.updateValueAndValidity();
      
    } else {
      this.countries = [];       // Clear countries if no region is selected

      this.supplierForm?.get('geo_region')?.clearValidators();
      this.supplierForm?.get('geo_region')?.updateValueAndValidity();
    }
  }

  onSubmit() {
    if (this.supplierForm.valid) {
      const formValue = { ...this.supplierForm.value };
      console.log('Final payload:', formValue);

      if (this.supplier_id && !this.from_hardware && !this.from_software) {
        // call update API
        this.masterDataService.updateSupplier(this.supplier_id, formValue).subscribe( data => {
          this.messageService.add({ severity: 'success', summary: '', detail: 'Supplier updated successfully' });
          setTimeout(() => {
              this.router.navigate(['/md/suppliers']);
          }, 1000);        
        },(err: any) => {
          this.activatedRouterService.updateError(err, this.messageService);      
        });
        
      } else {
        // call create API
        this.masterDataService.addSupplier(formValue).subscribe( data => {
          this.messageService.add({ severity: 'success', summary: '', detail: 'Supplier added successfully' });
          if(this.from_hardware) {
            this.supplier_for_hardware.emit(formValue);
          } else if (this.from_software) {
            this.supplier_for_software.emit(formValue);
          } else {            
            setTimeout(() => {
              this.router.navigate(['/md/suppliers']);
            }, 1000);
          }
        
        },(err: any) => {
          this.activatedRouterService.updateError(err, this.messageService);      
        }); 
      }
    } else {
      this.supplierForm.markAllAsTouched();
    }
  }

  onCancel() {
    this.supplierForm.reset();
    if(this.from_hardware) {
      this.supplier_for_hardware.emit(null);
    } else if (this.from_software) {
      this.supplier_for_software.emit(null);
    } else {
      this.router.navigate(['/md/suppliers']);
    }
  }
}
