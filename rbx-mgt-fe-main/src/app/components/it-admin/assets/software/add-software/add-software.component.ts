import { AccordionModule } from "primeng/accordion";
import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { AbstractControl, FormArray, FormBuilder, FormGroup, ReactiveFormsModule, ValidationErrors, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { CalendarModule } from 'primeng/calendar';
import { DropdownModule } from 'primeng/dropdown';
import { ToastModule } from "primeng/toast";
import { TableModule } from "primeng/table";
import { AllowOnlyCharDirective } from "src/app/directives/allow-only-char.directive";
import { AlphaNumericSpecialCharsDirective } from "src/app/directives/alphanumeric.directive";
import { DialogModule } from "primeng/dialog";
import { AddStatusComponent } from "src/app/components/master-data/it-admin/status/add-status/add-status.component";
import { AddSupplierComponent } from "src/app/components/master-data/it-admin/suppliers/add-supplier/add-supplier.component";
import { NumbersOnlyDirective } from "src/app/directives/numbers-only.directive";
import { MessageService } from "primeng/api";
import { ActivatedRouterService } from "src/app/services/activated-router-service";
import { MasterDataService } from "src/app/services/master-data.service";
import { AssetManagementService } from "src/app/services/asset-management.service";
import { retryWhen, delay, take, timeout, finalize } from 'rxjs/operators';

@Component({
  standalone: true,
  selector: 'app-add-software',
  templateUrl: './add-software.component.html',
  styleUrls: ['./add-software.component.scss'],
  imports: [DropdownModule, CalendarModule, ReactiveFormsModule, CommonModule,
    ToastModule, AccordionModule, TableModule, NumbersOnlyDirective, AllowOnlyCharDirective, AlphaNumericSpecialCharsDirective,
    DialogModule, AddStatusComponent, AddSupplierComponent]
})
export class AddSoftwareComponent {
  softwareForm!: FormGroup;
  software_id:string = ''
  page_title: string = '';
  btn_text: string = '';
  allAssetDetails:any = [];
  assetCategories:any = [];
  // assetCategoriesKeys:any = [];
  assetSubCategories:any = [];
  // previousUserName: string | null = null;
  maxSizeMB = 5;
  displayAddStatusDialog: boolean = false;
  displayAddSupplierDialog: boolean = false;
  purchaseCostTouched:boolean = false;
  showPassword: boolean = false;

  // dropdown data (replace with API calls)
  allCompaniesAndlocations:any = [];
  companies:any = [];
  locations:any = [];
  statuses:any = [];
  users:any = [];
  suppliers:any = [];

  currencyList = [
    { label: 'INR', value: 'INR' },
    { label: 'USD', value: 'USD' },
    { label: 'MYR', value: 'MYR' },
    { label: 'SGD', value: 'SGD' },
    { label: 'AED', value: 'AED' },
  ];

  selectedImageFile: any;
  selectedInvoiceFile: any;
  imgFile:any=[];
  invFile:any=[];

  softwareDetails:any = {};
  Assignment_Details:any[] = [];
  pdfUrl:string = '';
  imgFilePdfUrl: string = '';
  invFilePdfUrl: string = '';
  imgAvailable: boolean = false;
  invAvailable: boolean = false;
  isEmpLoading: boolean = false;

  maxDate:any;
  warrantyStatus = [ 
    { id: 'active', name: "Active" },
    { id: 'expired', name: "Expired" }
  ]

  constructor(private fb: FormBuilder,
              private router: Router,
              private activatedRoute: ActivatedRoute,
              private assetService: AssetManagementService,
              private messageService: MessageService,
              private activatedRouterService: ActivatedRouterService,
              private masterDataService: MasterDataService
  ) {
    this.activatedRoute.paramMap.subscribe(params => {
      this.software_id = params.get('id') || '';
    });
  }

  ngOnInit(): void {
    this.buildSoftwareForm();
    this.getAllEmployees();
    this.getCategories();
    this.getCompanies();
    this.getAllStatuses();
    this.getAllSuppliers();
    this.maxDate = new Date();

    // this.activatedRoute.paramMap.subscribe(params => {
    //   this.software_id = params.get('id') || '';
      if(this.software_id){
        this.getSoftwareDetails();
        this.btn_text='Update';
        this.page_title='Edit';
      } else{
        this.btn_text='Save';
        this.page_title='Add';
      }
    // });

    // Watch status and toggle validators    
    this.softwareForm.get('status')?.valueChanges.subscribe((status:any) => {
      this.softwareForm.patchValue({
        userName: '',
        fromDate: null,
        toDate: null
      });
    });

    //track purchase cost changes
    this.softwareForm.get('purchaseCost')?.valueChanges.subscribe(value => {
      if(value && value.toString().trim() !== '') {
        this.softwareForm.get('currency')?.setValidators([Validators.required]);
      } else {
        this.softwareForm.get('currency')?.clearValidators();
        this.softwareForm.get('currency')?.setValue(null, { emitEvent: false }); // clear dropdown
      }
      this.softwareForm.get('currency')?.updateValueAndValidity();
    })
  }

  buildSoftwareForm() {
    this.softwareForm = this.fb.group({
      //general data
      assetType: ['Software', Validators.required],
      asset_category: ['', Validators.required],
      asset_sub_category: ['', Validators.required],
      softwareName: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(40)]],
      quantity: ['', [Validators.required, Validators.maxLength(5)]],
      productKey: ['', [Validators.minLength(3), Validators.maxLength(50)]],
      assetTag: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(30)]],
      company: ['', Validators.required],
      assetId: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(30)]],
      licensedEmail: ['', [Validators.minLength(3), Validators.maxLength(50)]],
      status: ['', Validators.required],
      userName: ['', Validators.required],
      fromDate: [null, Validators.required],
      toDate: [null],
      notes: ['', [Validators.minLength(3), Validators.maxLength(80)]],
      location: ['', Validators.required],
      image: [''],

      //optional info
      warrantyStart: [null],
      warrantyEnd: [null],
      warrantyStatus: [''],
      amcStartDate: [''],
      amcEndDate: [''],
      amcVendor: ['', [Validators.minLength(3), Validators.maxLength(100)]],
      checkInDate: [null],
      byod: [false],

      //order info
      orderNumber: ['', [Validators.minLength(3), Validators.maxLength(20)]],
      purchaseDate: [null],
      supplier: [''],
      purchaseCost: ['', [Validators.maxLength(10)]],
      currency: [''],
      invoiceCopy: ['', [Validators.maxLength(50)]],

      //admin credentials
      adminUserName: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(20)]],
      adminPassword: ['', [Validators.required, Validators.minLength(6), Validators.maxLength(20)]],

      // assignment details are read-only
      // assignmentDetails: [],
      assignmentDetails: this.fb.array([]),

      // audit trail
      auditTrail: this.fb.group({
        lastChangedBy: [''],
        lastChangedDate: []
      })
    }, { validators: this.dateValidator });
  }

  onPurchaseCostBlur() {
    this.purchaseCostTouched = true;
  }

  getCategories() {
    this.assetService.getAllCategories('software').subscribe({
      next: (res:any) => {
        this.allAssetDetails = res['data'];
        this.assetCategories = this.allAssetDetails.map((item: any) => {
          const key = Object.keys(item)[0];
          return { name: key };
        });
      },
      error: (err:any) => {
        this.activatedRouterService.updateError(err, this.messageService)
      }
    })
  }

  getCompanies() {
    this.assetService.getAllCompanies().subscribe({
      next: (res:any) => {
        this.allCompaniesAndlocations = res;
        this.companies = this.allCompaniesAndlocations.map((item: any) => {
          const key = Object.keys(item)[0];
          return { name: key };
        });
      },
      error: (err:any) => {
        this.activatedRouterService.updateError(err, this.messageService)
      }
    })
  }

   getAllEmployees() {
    this.isEmpLoading = true;

    this.masterDataService.getActiveEmployeeDetails(true).subscribe({
      next:(res:any) => {
        this.users = (res?.data || [])
          // .filter((emp: any) => emp.status?.toLowerCase() === 'active')
          .sort((a: any, b: any) => {
            const dateA = new Date(a.updated_at || a.created_at).getTime();
            const dateB = new Date(b.updated_at || b.created_at).getTime();
            return dateB - dateA;
          })
          .map((emp: any) => ({
            label: emp.name,
            value: emp.name
          })
        );
        this.isEmpLoading = false;
      },
      error: (err:any) => {
        this.isEmpLoading = false;
        this.activatedRouterService.updateError(err, this.messageService);
      }
    })
  }

  onCategoryChange(type:string) {
    if(type=='onLoad') {
      //do nothing
    } else if(type=='onChange') {
      this.assetSubCategories = [];
      this.softwareForm.get('asset_sub_category')?.setValue([]);
    }
    
    const selectedCategory=this.softwareForm.get('asset_category')?.value;
    // console.log('selectedCategory:::', selectedCategory);

    if (selectedCategory) {
      // find the object in allAssetDetails that has this category as key
      const matched = this.allAssetDetails.find(
        (item: any) => Object.keys(item)[0] === selectedCategory
      );

      if (matched) {
        const subCats = matched[selectedCategory];
        this.assetSubCategories = subCats;

        // replace addValidators with setValidators to avoid duplicates,
        // reset value, update validity and mark as touched so UI shows required immediately
        const ctrl = this.softwareForm.get('asset_sub_category');
        ctrl?.setValidators([Validators.required]);
        ctrl?.updateValueAndValidity({ onlySelf: true, emitEvent: true });
        
        if(this.software_id) {//only if edit mode then apply
          ctrl?.markAsTouched();
          ctrl?.markAsDirty();
        }
        return;
      }
      
    } else {
      this.assetSubCategories = []; // Clear asset sub categories if no category is selected

      this.softwareForm?.get('asset_sub_category')?.clearValidators();
      this.softwareForm?.get('asset_sub_category')?.updateValueAndValidity();
    }
  }
  
  onCompanyChange(type:string) {
    if(type=='onLoad') {      
      //do nothing
    } else if(type=='onChange') {
      this.locations = [];
      this.softwareForm.get('location')?.setValue([]);
    }

    const selectedCompany=this.softwareForm.get('company')?.value;
    // console.log('selectedCompany:::', selectedCompany);

    if (selectedCompany) {
      // find the object in allCompaniesAndlocations that has this category as key
      const matched = this.allCompaniesAndlocations.find(
        (item: any) => Object.keys(item)[0] === selectedCompany
      );

      if (matched) {
        const loc = matched[selectedCompany];
        this.locations = loc;

        // replace addValidators with setValidators to avoid duplicates,
        // reset value, update validity and mark as touched so UI shows required immediately
        const ctrl = this.softwareForm.get('location');
        ctrl?.setValidators([Validators.required]);
        ctrl?.updateValueAndValidity({ onlySelf: true, emitEvent: true });
        
        if(this.software_id) {//only if edit mode then apply
          ctrl?.markAsTouched();
          ctrl?.markAsDirty();
        }
        return;
      }
      
    } else {
      this.locations = []; // Clear locations if no company is selected

      this.softwareForm?.get('location')?.clearValidators();
      this.softwareForm?.get('location')?.updateValueAndValidity();
    }
  }

  getAllStatuses() {
    this.masterDataService.getAllStatus().subscribe(res=>{
      this.statuses = res['data'].map((status:any) => ({
        label: status.status_name,
        value: status.status_name
      }));
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  getAllSuppliers() {
    this.masterDataService.getAllSuppliers().subscribe(res=>{
      this.suppliers = res['data'].map((supplier:any) => ({
        label: supplier.supplier,
        value: supplier.supplier
      }));
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  // Getter to access FormArray easily in template
  get assignmentDetails(): FormArray {
    return this.softwareForm.get('assignmentDetails') as FormArray;
  }

  getSoftwareDetails() {
    this.assetService.getSoftwareById(this.software_id).subscribe((res: any) => {
      this.softwareDetails = res['data'] || [];
      this.Assignment_Details = res['Assignment_Details'] || [];

      setTimeout(()=>{
        this.patchSoftwareForm(res);
      }, 500)
    });
  }

  patchSoftwareForm(res:any) {
    this.softwareForm.patchValue({
      "id": this.softwareDetails?.id,
      "assetType": "Software",
      "asset_category": this.softwareDetails?.asset_category ? this.softwareDetails?.asset_category : '',
      "asset_sub_category": this.softwareDetails?.asset_sub_category ? this.softwareDetails?.asset_sub_category : '',
      "softwareName": this.softwareDetails?.software_name ? this.softwareDetails?.software_name : '',
      "quantity": this.softwareDetails?.minimum_quantity ? this.softwareDetails?.minimum_quantity : '',
      "productKey": this.softwareDetails?.product_key ? this.softwareDetails?.product_key : '',
      "assetId": this.softwareDetails?.roboxa_asset_id ? this.softwareDetails?.roboxa_asset_id : '',
      "assetTag": this.softwareDetails?.asset_tag ? this.softwareDetails?.asset_tag : '',
      "company": this.softwareDetails?.company ? this.softwareDetails?.company : '',
      "licensedEmail": this.softwareDetails?.licensed_email ? this.softwareDetails?.licensed_email : '',
      "status": this.softwareDetails?.status ? this.softwareDetails?.status : '',
      "userName": this.softwareDetails?.user_name ? this.softwareDetails?.user_name : '',
      "fromDate": this.softwareDetails?.from_date ? new Date(this.softwareDetails?.from_date) : null,
      "toDate": null,
      "notes": this.softwareDetails?.notes ? this.softwareDetails?.notes : '',
      "location":   this.softwareDetails?.location ? this.softwareDetails?.location : '',
      "warrantyStart": this.softwareDetails?.warranty_start ? new Date(this.softwareDetails?.warranty_start) : null,
      "warrantyEnd": this.softwareDetails?.warranty_end ? new Date(this.softwareDetails?.warranty_end) : null,
      "warrantyStatus": this.softwareDetails?.warranty_status ? this.softwareDetails?.warranty_status : '',
      "amcStartDate": this.softwareDetails?.amc_start_date ? new Date(this.softwareDetails?.amc_start_date) : null,
      "amcEndDate": this.softwareDetails?.amc_end_date ? new Date(this.softwareDetails?.amc_end_date) : null,
      "amcVendor": this.softwareDetails?.amc_vendor ? this.softwareDetails?.amc_vendor : '',
      "checkInDate": this.softwareDetails?.check_in_date ? new Date(this.softwareDetails?.check_in_date) : null,
      "byod": this.softwareDetails?.byod,
      "orderNumber": this.softwareDetails?.order_number ? this.softwareDetails?.order_number : '',
      "purchaseDate": this.softwareDetails?.purchase_date ? new Date(this.softwareDetails?.purchase_date) : null,
      "supplier": this.softwareDetails?.supplier ? this.softwareDetails?.supplier : '',
      "purchaseCost": this.softwareDetails?.purchase_cost ? this.softwareDetails?.purchase_cost : '',
      "currency": this.softwareDetails?.currency ? this.softwareDetails?.currency : '',
      "adminUserName": this.softwareDetails?.admin_user_name ? this.softwareDetails?.admin_user_name : 'NA',
      "adminPassword": this.softwareDetails?.admin_password ? this.softwareDetails?.admin_password : 'NA',
      "lastChangedBy":  this.softwareDetails?.last_changed_by ? this.softwareDetails?.last_changed_by : 'NA',
      "lastChangedDate": this.softwareDetails?.last_changed_date ? this.softwareDetails?.last_changed_date : 'NA'
    });

    this.loadAssignmentDetails(this.Assignment_Details);

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

    this.onCategoryChange('onLoad');
    this.onCompanyChange('onLoad');
  }

  loadAssignmentDetails(details: any[]): void {
    details.forEach(d => {
      this.assignmentDetails.push(
        this.fb.group({
          userName: [d.user_name],
          status: [d.status],
          fromDate: [d.from_date],
          toDate: [d.to_date]
        })
      );
    });
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

  dateValidator(control: AbstractControl): ValidationErrors | null {
    const startDate = control.get('warrantyStart')?.value;
    const endDate = control.get('warrantyEnd')?.value;

    if (startDate && endDate) {
        const start = new Date(startDate);
        const end = new Date(endDate);

        // Compare year, month, and day
        if (end.getTime() < start.getTime()) {
            return { endDateLessThanStartDate: true };
        }
    }
    return null;
  }

  changeFormat(dateToTransfer:string){
    const date = new Date(dateToTransfer);
    const formattedDate = date.getFullYear() + '-' +
      String(date.getMonth() + 1).padStart(2, '0') + '-' +
      String(date.getDate()).padStart(2, '0');
    return formattedDate
  }

  testEnddate(end_date:any,start_date:any){
    this.dateValidator(this.softwareForm);
    if(start_date.value>end_date.value){
      // this.messageService.add({ severity: 'error', summary: 'Date validation Error', detail: 'End date must be greater than start date.' });
    }
  }

  onFileSelect(event: Event, section:string) {
    const input = event.target as HTMLInputElement;
    let fileType1;
    let fileType2;

    if (input.files?.length) {
      if(section == 'image') {
        this.imgFile=input.files;
        this.selectedImageFile = input.files[0];
        fileType1 = this.selectedImageFile.type;

        if (fileType1 !== 'application/pdf' && fileType1 !== 'image/jpeg') {
          alert('Only PDF or JPEG files are allowed');
          this.softwareForm.patchValue({ image: null });
          input.value = '';
          return;
        }

        if (this.selectedImageFile.size > this.maxSizeMB * 1024 * 1024) {
          alert(`File size exceeds ${this.maxSizeMB}MB`);
          this.softwareForm.patchValue({ image: null });
          input.value = '';
          return;
        }
        
      } else if (section == 'invoice') {
        this.invFile=input.files;
        this.selectedInvoiceFile = input.files[0];
        fileType2 = this.selectedInvoiceFile.type;

        if (fileType2 !== 'application/pdf' && fileType2 !== 'image/jpeg') {
          alert('Only PDF or JPEG files are allowed');
          this.softwareForm.patchValue({ invoiceCopy: null });
          input.value = '';
          return;
        }
        
        if (this.selectedInvoiceFile.size > this.maxSizeMB * 1024 * 1024) {
          alert(`File size exceeds ${this.maxSizeMB}MB`);
          this.softwareForm.patchValue({ invoiceCopy: null });
          input.value = '';
          return;
        }
      }
    }
  }

  onAddStatus() {
    this.displayAddStatusDialog = true;
  }

  onStatusAdded(newStatus: any) {
    if(newStatus) {
      this.statuses.push({ label: newStatus.status_name, value: newStatus.status_name }); // update dropdown
      // console.log(this.statuses)
      this.softwareForm.patchValue({ status: newStatus.status_name }); // optionally select the new model
    }
    
    this.displayAddStatusDialog = false;
  }

  onAddSupplier() {
  this.displayAddSupplierDialog = true;
  }

  onSupplierAdded(newSupplier: any) {
    if(newSupplier) {
      this.suppliers.push({ label: newSupplier.supplier, value: newSupplier.supplier }); // update dropdown
      // console.log(this.suppliers)
      this.softwareForm.patchValue({ supplier: newSupplier.supplier }); // optionally select the new supplier
    }
    
    this.displayAddSupplierDialog = false;
  }

  togglePasswordVisibility() {
    this.showPassword = !this.showPassword;
  }

  onSubmit() {
    // console.log(this.softwareForm);
    const formData = new FormData();
    formData.append('asset_type ', this.softwareForm.get('assetType')?.value);
    formData.append('asset_category ', this.softwareForm.get('asset_category')?.value);
    formData.append('asset_sub_category ', this.softwareForm.get('asset_sub_category')?.value);
    formData.append('software_name ', this.softwareForm.get('softwareName')?.value);
    formData.append('minimum_quantity  ', this.softwareForm.get('quantity')?.value);
    formData.append('product_key  ', this.softwareForm.get('productKey')?.value);
    formData.append('roboxa_asset_id ', this.softwareForm.get('assetId')?.value);
    formData.append('asset_tag ', this.softwareForm.get('assetTag')?.value);
    formData.append('company', this.softwareForm.get('company')?.value);
    formData.append('licensed_email', this.softwareForm.get('licensedEmail')?.value);
    formData.append('status', this.softwareForm.get('status')?.value);
    formData.append('user_name ', this.softwareForm.get('userName')?.value);
    formData.append('notes', this.softwareForm.get('notes')?.value);
    formData.append('location', this.softwareForm.get('location')?.value);

    formData.append('warranty_status', this.softwareForm.get('warrantyStatus')?.value);
    formData.append('amc_vendor', this.softwareForm.get('amcVendor')?.value);
    formData.append('byod', this.softwareForm.get('byod')?.value || false);

    formData.append('order_number', this.softwareForm.get('orderNumber')?.value);
    formData.append('supplier', this.softwareForm.get('supplier')?.value);
    formData.append('purchase_cost', this.softwareForm.get('purchaseCost')?.value);
    formData.append('currency', this.softwareForm.get('currency')?.value);

    formData.append('admin_user_name', this.softwareForm.get('adminUserName')?.value);
    formData.append('admin_password', this.softwareForm.get('adminPassword')?.value);

    const fromDate = this.softwareForm.get('fromDate')?.value;
    if (fromDate) {
      formData.append('from_date', this.changeFormat(fromDate));
    }

    const warrantyStart = this.softwareForm.get('warrantyStart')?.value;
    if (warrantyStart) {
      formData.append('warranty_start_date', this.changeFormat(warrantyStart));
    }

    const warrantyEnd = this.softwareForm.get('warrantyEnd')?.value;
    if (warrantyEnd) {
      formData.append('warranty_end_date', this.changeFormat(warrantyEnd));
    }

    const amcStartDate = this.softwareForm.get('amcStartDate')?.value;
    if (amcStartDate) {
      formData.append('amc_start_date', this.changeFormat(amcStartDate));
    }

    const amcEndDate = this.softwareForm.get('amcEndDate')?.value;
    if (amcEndDate) {
      formData.append('amc_end_date', this.changeFormat(amcEndDate));
    }

    const checkInDate = this.softwareForm.get('checkInDate')?.value;
    if (checkInDate) {
      formData.append('check_in_date', this.changeFormat(checkInDate));
    }

    const purchaseDate = this.softwareForm.get('purchaseDate')?.value;
    if (purchaseDate) {
      formData.append('purchase_date', this.changeFormat(purchaseDate));
    }

    if(this.imgFile?.length !=0) {
      formData.append('image', this.selectedImageFile);
    }

    if(this.invFile?.length !=0) {
      formData.append('invoice_copy', this.selectedInvoiceFile);
    }
    
    if (this.softwareForm.valid) {
      if (this.software_id) {
        // call update API
        this.assetService.updateSoftware(this.software_id, formData).subscribe({
          next: (res:any) => {
            this.messageService.add({ severity: 'success', summary: '', detail: 'Software details updated successfully' });
            this.router.navigate(['/IT/software']);
          },
          error: (err:any) => {
             this.activatedRouterService.updateError(err, this.messageService);
          }
        });

      } else {        
        // call create API
        this.assetService.addSoftware(formData).subscribe({
          next: (res:any) => {
            this.messageService.add({ severity: 'success', summary: '', detail: 'Software details added successfully' });
            this.router.navigate(['/IT/software']);
          },
          error: (err:any) => {
             this.activatedRouterService.updateError(err, this.messageService);
          }
        });      
      }
    }
  }

  onCancel() {
    this.softwareForm.reset();
    this.router.navigate(['/IT/software']);
  }

  getFormValidation() {
    const controls = this.softwareForm.controls;  
    const basicFieldsValid =  controls['assetType'].value &&
                              controls['asset_category'].value &&
                              controls['asset_sub_category'].value &&
                              controls['softwareName'].value &&
                              controls['quantity'].value &&
                              controls['assetId'].value &&
                              controls['assetTag'].value &&
                              controls['company'].value &&
                              controls['status'].value &&
                              controls['userName'].value &&
                              controls['fromDate'].value &&
                              controls['location'].value &&
                              controls['adminUserName'].value &&
                              controls['adminPassword'].value
    
    const purchaseCost = this.softwareForm.get('purchaseCost')?.value;
    if(purchaseCost && purchaseCost.toString().trim() !== '') {
      return basicFieldsValid && !!controls['currency'].value;
    } else {
      return basicFieldsValid;
    }
  }
}