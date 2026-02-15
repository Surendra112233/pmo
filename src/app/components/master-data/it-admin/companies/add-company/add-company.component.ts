import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormArray, FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { MessageService } from 'primeng/api';
import { DropdownModule } from 'primeng/dropdown';
import { timer } from 'rxjs';
import { AlphaNumericSpecialCharsDirective } from 'src/app/directives/alphanumeric.directive';
import { ActivatedRouterService } from 'src/app/services/activated-router-service';
import { LoginService } from 'src/app/services/login.service';
import { MasterDataService } from 'src/app/services/master-data.service';

@Component({
  standalone: true,
  selector: 'app-add-company',
  templateUrl: './add-company.component.html',
  styleUrls: ['./add-company.component.scss'],
  imports: [ReactiveFormsModule, CommonModule, DropdownModule, AlphaNumericSpecialCharsDirective]
})
export class AddCompanyComponent implements OnInit {
  companyForm!: FormGroup;
  regions:any[]=[];
  countriesByRegion:any[]=[];
  countries:any[]=[];
  company_id:string = '';
  btn_text:string = '';
  page_title:string = '';
  timer$ = timer(500);

  constructor(private fb: FormBuilder,
              private loginService: LoginService,
              private router: Router,
              private activatedRoute: ActivatedRoute,
              private masterDataService: MasterDataService,
              private messageService: MessageService,
              private activatedRouterService: ActivatedRouterService
  ) {}

  ngOnInit() {
    this.buildCompanyForm();
    this.getDropDownData();

    this.activatedRoute.paramMap.subscribe(params => {
      this.company_id = params.get('id') || '';
      if(this.company_id){
        this.getCompanyDetails();
        // this.timer$.subscribe(res => this.getCompanyDetails());
        this.btn_text='Update';
        this.page_title='Edit';
      } else{
       this.btn_text='Save';
       this.page_title='Add';
      }
    });
  }
  
  buildCompanyForm() {
    this.companyForm = this.fb.group({
      company: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(50)]],
      address: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(80)]],
      country: ['', Validators.required],
      geo_region: ['', Validators.required],
      location_name: this.fb.array([]),
      locationInput: ['']
    });
  }

  getDropDownData() {
    this.loginService.getDropdownData().subscribe(data => {     
      this.regions=data.Regions;
      this.countriesByRegion=data.CountriesByRegion;
    });
  }

  getCompanyDetails() {
    this.masterDataService.getCompanyById(this.company_id).subscribe((res: any) => {
      let data = res['data'];

      // patch main fields
      this.companyForm.patchValue({
        company: data.company,
        address: data.address,
        geo_region: data.geo_region,
        country: data.country
      });

      // clear and repopulate chips 
      this.locationNames.clear(); 
      if (data.location_name && Array.isArray(data.location_name)) { 
        data.location_name.forEach((loc: string) => { 
          this.locationNames.push(this.fb.control(loc)); 
        }); 
      }

      this.onRegionChange('onLoad');
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  get locationNames(): FormArray {
    return this.companyForm.get('location_name') as FormArray;
  }

  addLocationFromInput() {
    const inputControl = this.companyForm.get('locationInput');
    const value = inputControl?.value?.trim();

    if (value) {
      this.locationNames.push(this.fb.control(value, [Validators.maxLength(60)]));
      inputControl?.reset(); // clear input
    }
  }

  removeLocation(index: number) {
    this.locationNames.removeAt(index);
  }

  onRegionChange(type:string) {
    if(type=='onLoad') {
      //do nothing
    } else if(type=='onChange') {
      this.companyForm.get('country')?.setValue([]);
    }
    const selectedRegion=this.companyForm.get('geo_region')?.value;
    console.log('selectedRegion:::', selectedRegion);

    // Update the countries based on the selected region
    if (selectedRegion && this.countriesByRegion[selectedRegion]) {
      this.countries = this.countriesByRegion[selectedRegion]; // Populate countries based on region
      console.log('this.countries:::', this.countries);
      this.companyForm?.get('country')?.addValidators(Validators.required);
      this.companyForm?.get('country')?.updateValueAndValidity();
      
    } else {
      this.countries = [];       // Clear countries if no region is selected

      this.companyForm?.get('geo_region')?.clearValidators();
      this.companyForm?.get('geo_region')?.updateValueAndValidity();
    }
  }

  onSubmit() {
    if (this.companyForm.valid) {
      const formValue = { ...this.companyForm.value };
      // formValue.location_name = formValue.location_name.join(', ');
      delete formValue.locationInput; // remove temp field
      console.log('Final payload:', formValue);

      if (this.company_id) {
        // call update API
        this.masterDataService.updateCompany(this.company_id, formValue).subscribe( data => {
          this.messageService.add({ severity: 'success', summary: '', detail: 'Company updated successfully' });
          setTimeout(() => {
              this.router.navigate(['/md/companies']);
          }, 1000);        
        },(err: any) => {
          this.activatedRouterService.updateError(err, this.messageService);      
        });
      } else {
        // call create API
        this.masterDataService.addCompany(formValue).subscribe( data => {
          this.messageService.add({ severity: 'success', summary: '', detail: 'Company added successfully' });    
          setTimeout(() => {
            this.router.navigate(['/md/companies']);
          }, 1000);
        
        },(err: any) => {
          this.activatedRouterService.updateError(err, this.messageService);      
        });        
      }
    } else {
      this.companyForm.markAllAsTouched();
    }
  }

  onCancel() {
    this.companyForm.reset();
    this.locationNames.clear();
    this.router.navigate(['/md/companies']);
  }
}
