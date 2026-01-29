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
import { AddAssetModelComponent } from "src/app/components/master-data/it-admin/asset-models/add-asset-model/add-asset-model.component";
import { DialogModule } from "primeng/dialog";
import { AddStatusComponent } from "src/app/components/master-data/it-admin/status/add-status/add-status.component";
import { AddSupplierComponent } from "src/app/components/master-data/it-admin/suppliers/add-supplier/add-supplier.component";
import { NumbersOnlyDirective } from "src/app/directives/numbers-only.directive";
import { AssetManagementService } from "src/app/services/asset-management.service";
import { MessageService } from "primeng/api";
import { ActivatedRouterService } from "src/app/services/activated-router-service";
import { MasterDataService } from "src/app/services/master-data.service";
import { retryWhen, delay, take, timeout, finalize } from 'rxjs/operators';

@Component({
  standalone: true,
  selector: 'app-add-hardware',
  templateUrl: './add-hardware.component.html',
  styleUrls: ['./add-hardware.component.scss'],
  imports: [DropdownModule, CalendarModule, ReactiveFormsModule, CommonModule,
    ToastModule, AccordionModule, TableModule, NumbersOnlyDirective, AllowOnlyCharDirective, AlphaNumericSpecialCharsDirective,
    AddAssetModelComponent, DialogModule, AddStatusComponent, AddSupplierComponent]
})
export class AddHardwareComponent {
  hardwareForm!: FormGroup;
  hardware_id:string = ''
  page_title: string = '';
  btn_text: string = '';
  allAssetDetails:any = {};
  assetCategories:any = [];
  // assetCategoriesKeys:any = [];
  assetSubCategories:any = [];
  // previousUserName: string | null = null;
  maxSizeMB = 5;
  displayAddModelDialog: boolean = false;
  displayAddStatusDialog: boolean = false;
  displayAddSupplierDialog: boolean = false;
  purchaseCostTouched:boolean = false;
  showPassword: boolean = false;

  // dropdown data (replace with API calls)
  allCompaniesAndlocations:any = [];
  companies:any = [];
  locations:any = [];
  models:any = [];
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

  hardwareDetails:any = {};
  // Assignment_Details:any[] = [];
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
      this.hardware_id = params.get('id') || '';
    });
  }

  ngOnInit(): void {   
    this.buildHardwareForm();
    this.getAllEmployees();
    this.getCategories();
    this.getCompanies();
    this.getAllModels();
    this.getAllStatuses();
    this.getAllSuppliers();
    this.maxDate = new Date();

    // this.activatedRoute.paramMap.subscribe(params => {
    //   this.hardware_id = params.get('id') || '';
      if(this.hardware_id){
        this.getHardwareDetails();
        this.btn_text='Update';
        this.page_title='Edit';
      } else{
        this.btn_text='Save';
        this.page_title='Add';
      }
    // });

    // Watch status and toggle validators    
    this.hardwareForm.get('status')?.valueChanges.subscribe((status:any) => {
      this.hardwareForm.patchValue({
        userName: '',
        fromDate: null,
        toDate: null
      });
    });

    //track purchase cost changes
    this.hardwareForm.get('purchaseCost')?.valueChanges.subscribe(value => {
      if(value && value.toString().trim() !== '') {
        this.hardwareForm.get('currency')?.setValidators([Validators.required]);
      } else {
        this.hardwareForm.get('currency')?.clearValidators();
        this.hardwareForm.get('currency')?.setValue(null, { emitEvent: false }); // clear dropdown
      }
      this.hardwareForm.get('currency')?.updateValueAndValidity();
    })

    // dynamic validators: when external === true
    this.hardwareForm.get('external')?.valueChanges.subscribe((isExternal:any) => {
      const transferFromCtrl = this.hardwareForm.get('transferFrom');
      const transferFromDateCtrl = this.hardwareForm.get('transferFromDate');
      const transferToCtrl = this.hardwareForm.get('transferTo');
      const transferToDateCtrl = this.hardwareForm.get('transferToDate');

      if (isExternal) {
        transferFromCtrl?.setValidators([Validators.required, Validators.minLength(3), Validators.maxLength(40)]);
        transferFromDateCtrl?.setValidators([Validators.required]);
        transferToCtrl?.setValidators([Validators.required, Validators.minLength(3), Validators.maxLength(40)]);
        transferToDateCtrl?.setValidators([Validators.required]);
      } else {
        transferFromCtrl?.clearValidators();
        transferFromDateCtrl?.clearValidators();
        transferToCtrl?.clearValidators();
        transferToDateCtrl?.clearValidators();
      }

      // keep current value but ensure validity recalculated
      transferFromCtrl?.updateValueAndValidity({ onlySelf: true, emitEvent: false });
      transferFromDateCtrl?.updateValueAndValidity({ onlySelf: true, emitEvent: false });
      transferToCtrl?.updateValueAndValidity({ onlySelf: true, emitEvent: false });
      transferToDateCtrl?.updateValueAndValidity({ onlySelf: true, emitEvent: false });

      // if in edit mode and now required, mark touched so UI shows errors immediately
      if (isExternal && this.hardware_id) {
        transferFromCtrl?.markAsTouched();
        transferFromDateCtrl?.markAsTouched();
        transferToCtrl?.markAsTouched();
        transferToDateCtrl?.markAsTouched();
      }
    });
  }

  buildHardwareForm() {
    this.hardwareForm = this.fb.group({
      //general data
      assetType: ['Hardware', Validators.required],
      assetCategory: ['', Validators.required],
      assetSubCategory: ['', Validators.required],
      assetName: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(40)]],
      company: ['', Validators.required],
      assetId: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(30)]],
      configDetails: ['', [Validators.minLength(3), Validators.maxLength(100)]],
      external: [false],
      transferFrom: ['', [Validators.minLength(3), Validators.maxLength(40)]],
      transferFromDate: [''],
      transferTo: ['', [Validators.minLength(3), Validators.maxLength(40)]],
      transferToDate: [''],
      assetTag: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(30)]],
      serialNumber: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(30)]],
      model: ['', Validators.required],
      status: ['', Validators.required],
      userName: ['', Validators.required],
      fromDate: ['', Validators.required],
      toDate: [''],
      notes: ['', [Validators.minLength(3), Validators.maxLength(80)]],
      location: ['', Validators.required],
      image: [''],

      //optional info
      warrantyStart: [''],
      warrantyEnd: [''],
      warrantyStatus: [''],
      amcStartDate: [''],
      amcEndDate: [''],
      amcVendor: ['', [Validators.minLength(3), Validators.maxLength(100)]],
      checkInDate: [''],
      byod: [false],

      //order info
      orderNumber: ['', [Validators.minLength(3), Validators.maxLength(20)]],
      purchaseDate: [''],
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
    this.assetService.getAllCategories('hardware').subscribe({
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
      this.hardwareForm.get('assetSubCategory')?.setValue([]);
    }
    
    const selectedCategory=this.hardwareForm.get('assetCategory')?.value;
    if (selectedCategory) {
      // find the object in allAssetDetails that has this category as key
      const matched = this.allAssetDetails.find(
        (item: any) => Object.keys(item)[0] === selectedCategory
      );

      if (matched) {
        const subCats = matched[selectedCategory];
        this.assetSubCategories = subCats;

        const ctrl = this.hardwareForm.get('assetSubCategory');
        ctrl?.setValidators([Validators.required]);
        ctrl?.updateValueAndValidity({ onlySelf: true, emitEvent: true });
        
        if(this.hardware_id) {//only if edit mode then apply
          ctrl?.markAsTouched();
          ctrl?.markAsDirty();
        }
        return;
      }
      
    } else {
      this.assetSubCategories = []; // Clear asset sub categories if no category is selected

      this.hardwareForm?.get('assetSubCategory')?.clearValidators();
      this.hardwareForm?.get('assetSubCategory')?.updateValueAndValidity();
    }
  }

  onCompanyChange(type:string) {
    if(type=='onLoad') {
      //do nothing
    } else if(type=='onChange') {
      this.locations = [];
      this.hardwareForm.get('location')?.setValue([]);
    }
    
    const selectedCompany=this.hardwareForm.get('company')?.value;
    if (selectedCompany) {
      // find the object in allCompaniesAndlocations that has this category as key
      const matched = this.allCompaniesAndlocations.find(
        (item: any) => Object.keys(item)[0] === selectedCompany
      );

      if (matched) {
        const loc = matched[selectedCompany];
        this.locations = loc;
        
        const ctrl = this.hardwareForm.get('location');
        ctrl?.setValidators([Validators.required]);
        ctrl?.updateValueAndValidity({ onlySelf: true, emitEvent: true });
        
        if(this.hardware_id) {//only if edit mode then apply
          ctrl?.markAsTouched();
          ctrl?.markAsDirty();
        }
        return;
      }
      
    } else {
      this.locations = []; // Clear locations if no company is selected

      this.hardwareForm?.get('location')?.clearValidators();
      this.hardwareForm?.get('location')?.updateValueAndValidity();
    }
  }

  getAllModels() {
    this.masterDataService.getAllAssetModels().subscribe(res=>{
      this.models = res['data'].map((model:any) => ({
        label: model.asset_model_name,
        value: model.asset_model_name
      }));
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })
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
    return this.hardwareForm.get('assignmentDetails') as FormArray;
  }

  getHardwareDetails() {
     this.assetService.getHardwareById(this.hardware_id).subscribe((res: any) => {
      this.hardwareDetails = res['data'] || [];
      // this.Assignment_Details = res['Assignment_Details'] || [];

      setTimeout(()=>{
        this.patcHardwareForm(res);
      }, 500)
    });
  }

  patcHardwareForm(res:any) {    
    this.hardwareForm.patchValue({
      "id": this.hardwareDetails.id,
      "assetType": "Hardware",
      "assetCategory": this.hardwareDetails?.assetCategory ? this.hardwareDetails?.assetCategory : '',
      "assetSubCategory": this.hardwareDetails?.assetSubCategory ? this.hardwareDetails?.assetSubCategory : '',
      "assetName": this.hardwareDetails?.assetName ? this.hardwareDetails?.assetName : '',
      "company": this.hardwareDetails?.company ? this.hardwareDetails?.company : '',
      "assetId": this.hardwareDetails?.roboxaAssetId ? this.hardwareDetails?.roboxaAssetId : '',
      "configDetails": this.hardwareDetails?.configurationDetails ? this.hardwareDetails?.configurationDetails : '',
      "external": this.hardwareDetails?.external ? this.hardwareDetails?.external : '',
      "transferFrom": this.hardwareDetails?.transferFrom ? this.hardwareDetails?.transferFrom : '',
      "transferFromDate": this.hardwareDetails?.transferFromDate ? new Date(this.hardwareDetails?.transferFromDate) : null,
      "transferTo": this.hardwareDetails?.transferTo ? this.hardwareDetails?.transferTo : '',
      "transferToDate": this.hardwareDetails?.transferToDate ? new Date(this.hardwareDetails?.transferToDate) : null,
      "assetTag": this.hardwareDetails?.assetTag ? this.hardwareDetails?.assetTag : '',
      "serialNumber": this.hardwareDetails?.serialNumber ? this.hardwareDetails?.serialNumber : '',
      "model": this.hardwareDetails?.model ? this.hardwareDetails?.model : '',
      "status": this.hardwareDetails?.status ? this.hardwareDetails?.status : '',
      "userName": this.hardwareDetails?.userName ? this.hardwareDetails?.userName : '',
      "fromDate": this.hardwareDetails?.fromDate ? new Date(this.hardwareDetails?.fromDate) : null,
      "toDate": null,
      "notes": this.hardwareDetails?.notes ? this.hardwareDetails?.notes : '',
      "location": this.hardwareDetails?.location ? this.hardwareDetails?.location : '',
      "warrantyStart": this.hardwareDetails?.warrantyStart ? new Date(this.hardwareDetails?.warrantyStart) : null,
      "warrantyEnd": this.hardwareDetails?.warrantyEnd ? new Date(this.hardwareDetails?.warrantyEnd) : null,
      "warrantyStatus": this.hardwareDetails?.warrantyStatus ? this.hardwareDetails?.warrantyStatus : '',
      "amcStartDate": this.hardwareDetails?.amcStartDate ? new Date(this.hardwareDetails?.amcStartDate) : null,
      "amcEndDate": this.hardwareDetails?.amcEndDate ? new Date(this.hardwareDetails?.amcEndDate) : null,
      "amcVendor": this.hardwareDetails?.amcVendor ? this.hardwareDetails?.amcVendor : '',
      "checkInDate": this.hardwareDetails?.checkInDate ? new Date(this.hardwareDetails?.checkInDate) : null,
      "byod": this.hardwareDetails?.byod ? this.hardwareDetails?.byod : '',
      "orderNumber": this.hardwareDetails?.orderNumber ? this.hardwareDetails?.orderNumber : '',
      "purchaseDate": this.hardwareDetails?.purchaseDate ? new Date(this.hardwareDetails?.purchaseDate) : null,
      "supplier": this.hardwareDetails?.supplier ? this.hardwareDetails?.supplier : '',
      "purchaseCost": this.hardwareDetails?.purchaseCost ? this.hardwareDetails?.purchaseCost : '',
      "currency": this.hardwareDetails?.currency ? this.hardwareDetails?.currency : '',
      "adminUserName": this.hardwareDetails?.adminUserName ? this.hardwareDetails?.adminUserName : 'NA',
      "adminPassword": this.hardwareDetails?.adminPassword ? this.hardwareDetails?.adminPassword : 'NA',
      "auditTrail": {
        "lastChangedBy": this.hardwareDetails?.auditTrail?.lastChangedBy ? this.hardwareDetails?.auditTrail?.lastChangedBy : 'NA',
        "lastChangedDate": this.hardwareDetails?.auditTrail?.lastChangedDate ? this.hardwareDetails?.auditTrail?.lastChangedDate : 'NA',
      }
    });

    this.loadAssignmentDetails(this.hardwareDetails?.assignmentDetails);
    
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
          userName: [d.userName],
          status: [d.status],
          fromDate: [d.fromDate],
          toDate: [d.toDate]
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
    this.dateValidator(this.hardwareForm);
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
          this.hardwareForm.patchValue({ image: null });
          input.value = '';
          return;
        }

        if (this.selectedImageFile.size > this.maxSizeMB * 1024 * 1024) {
          alert(`File size exceeds ${this.maxSizeMB}MB`);
          this.hardwareForm.patchValue({ image: null });
          input.value = '';
          return;
        }
        
      } else if (section == 'invoice') {
        this.invFile=input.files;
        this.selectedInvoiceFile = input.files[0];
        fileType2 = this.selectedInvoiceFile.type;

        if (fileType2 !== 'application/pdf' && fileType2 !== 'image/jpeg') {
          alert('Only PDF or JPEG files are allowed');
          this.hardwareForm.patchValue({ invoiceCopy: null });
          input.value = '';
          return;
        }
        
        if (this.selectedInvoiceFile.size > this.maxSizeMB * 1024 * 1024) {
          alert(`File size exceeds ${this.maxSizeMB}MB`);
          this.hardwareForm.patchValue({ invoiceCopy: null });
          input.value = '';
          return;
        }
      }
    }
  }

  onAddModel() {
    this.displayAddModelDialog = true;
  }

  onModelAdded(newModel: any) {
    if(newModel) {
      this.models.push({ label: newModel.asset_model_name, value: newModel.asset_model_name }); // update dropdown
      // console.log(this.models)
      this.hardwareForm.patchValue({ model: newModel.asset_model_name }); // optionally select the new model
    }
    
    this.displayAddModelDialog = false;
  }

  onAddStatus() {
    this.displayAddStatusDialog = true;
  }

  onStatusAdded(newStatus: any) {
    if(newStatus) {
      this.statuses.push({ label: newStatus.status_name, value: newStatus.status_name }); // update dropdown
      // console.log(this.statuses)
      this.hardwareForm.patchValue({ status: newStatus.status_name }); // optionally select the new model
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
      this.hardwareForm.patchValue({ supplier: newSupplier.supplier }); // optionally select the new supplier
    }
    
    this.displayAddSupplierDialog = false;
  }

  togglePasswordVisibility() {
    this.showPassword = !this.showPassword;
  }

  onSubmit() {
    // console.log(this.hardwareForm);
    const formData = new FormData();
    formData.append('asset_type ', this.hardwareForm.get('assetType')?.value);
    formData.append('asset_category', this.hardwareForm.get('assetCategory')?.value);
    formData.append('asset_sub_category ', this.hardwareForm.get('assetSubCategory')?.value);
    formData.append('asset_name', this.hardwareForm.get('assetName')?.value);
    formData.append('company', this.hardwareForm.get('company')?.value);
    formData.append('roboxa_asset_id ', this.hardwareForm.get('assetId')?.value);
    formData.append('configuration_details ', this.hardwareForm.get('configDetails')?.value);
    formData.append('external', this.hardwareForm.get('external')?.value || false);
    formData.append('transfer_from ', this.hardwareForm.get('transferFrom')?.value);
    formData.append('transfer_to ', this.hardwareForm.get('transferTo')?.value);
    formData.append('asset_tag ', this.hardwareForm.get('assetTag')?.value);
    formData.append('serial_number ', this.hardwareForm.get('serialNumber')?.value);
    formData.append('model', this.hardwareForm.get('model')?.value);
    formData.append('status', this.hardwareForm.get('status')?.value);
    formData.append('user_name ', this.hardwareForm.get('userName')?.value);
    formData.append('notes', this.hardwareForm.get('notes')?.value);
    formData.append('location', this.hardwareForm.get('location')?.value);

    formData.append('warranty_status', this.hardwareForm.get('warrantyStatus')?.value);
    formData.append('amc_vendor', this.hardwareForm.get('amcVendor')?.value);
    formData.append('byod', this.hardwareForm.get('byod')?.value || false);

    formData.append('order_number', this.hardwareForm.get('orderNumber')?.value);
    formData.append('supplier', this.hardwareForm.get('supplier')?.value);
    formData.append('purchase_cost', this.hardwareForm.get('purchaseCost')?.value);
    formData.append('currency', this.hardwareForm.get('currency')?.value);

    formData.append('admin_user_name ', this.hardwareForm.get('adminUserName')?.value);
    formData.append('admin_password ', this.hardwareForm.get('adminPassword')?.value);
    // console.log('FormData entries:', formData);

    const transferFromDate = this.hardwareForm.get('transferFromDate')?.value;
    if (transferFromDate) {
      formData.append('transfer_from_date ', this.changeFormat(transferFromDate));
    }

    const transferToDate = this.hardwareForm.get('transferToDate')?.value;
    if (transferToDate) {
      formData.append('transfer_to_date ', this.changeFormat(transferToDate));
    }

    const fromDate = this.hardwareForm.get('fromDate')?.value;
    if (fromDate) {
      formData.append('from_date ', this.changeFormat(fromDate));
    }

    const warrantyStart = this.hardwareForm.get('warrantyStart')?.value;
    if (warrantyStart) {
      formData.append('warranty_start_date', this.changeFormat(warrantyStart));
    }

    const warrantyEnd = this.hardwareForm.get('warrantyEnd')?.value;
    if (warrantyEnd) {
      formData.append('warranty_end_date', this.changeFormat(warrantyEnd));
    }

    const amcStartDate = this.hardwareForm.get('amcStartDate')?.value;
    if (amcStartDate) {
      formData.append('amc_start_date', this.changeFormat(amcStartDate));
    }

    const amcEndDate = this.hardwareForm.get('amcEndDate')?.value;
    if (amcEndDate) {
      formData.append('amc_end_date', this.changeFormat(amcEndDate));
    }

    const checkInDate = this.hardwareForm.get('checkInDate')?.value;
    if (checkInDate) {
      formData.append('check_in_date', this.changeFormat(checkInDate));
    }

    const purchaseDate = this.hardwareForm.get('purchaseDate')?.value;
    if (purchaseDate) {
      formData.append('purchase_date', this.changeFormat(purchaseDate));
    }

    if(this.imgFile?.length !=0) {
      formData.append('image', this.selectedImageFile);
    }

    if(this.invFile?.length !=0) {
      formData.append('invoice_copy', this.selectedInvoiceFile);
    }

    if (this.hardwareForm.valid) {
      // console.log('Form Submitted:', this.hardwareForm.value);

      if (this.hardware_id) {
        // call update API
        this.assetService.updateHardware(this.hardware_id, formData).subscribe({
          next: (res:any) => {
            this.messageService.add({ severity: 'success', summary: '', detail: 'Hardware details updated successfully' });
            this.router.navigate(['/IT/hardware']);
          },
          error: (err:any) => {
             this.activatedRouterService.updateError(err, this.messageService);
          }
        });

      } else {        
        // call create API
        this.assetService.addHardware(formData).subscribe({
          next: (res:any) => {
            this.messageService.add({ severity: 'success', summary: '', detail: 'Hardware details added successfully' });
            this.router.navigate(['/IT/hardware']);
          },
          error: (err:any) => {
             this.activatedRouterService.updateError(err, this.messageService);
          }
        });  
      }
    }
  }

  onCancel() {
    this.hardwareForm.reset();
    this.router.navigate(['/IT/hardware']);
  }

  getFormValidation() {
    const controls = this.hardwareForm.controls;  
    const basicFieldsValid =  controls['assetType'].value &&
                              controls['assetCategory'].value &&
                              controls['assetSubCategory'].value &&
                              controls['assetName'].value &&
                              controls['company'].value &&
                              controls['assetId'].value &&
                              controls['assetTag'].value &&
                              controls['serialNumber'].value &&
                              controls['model'].value &&
                              controls['status'].value &&
                              controls['userName'].value &&
                              controls['fromDate'].value &&
                              controls['location'].value &&
                              controls['adminUserName'].value &&
                              controls['adminPassword'].value
    
    // if external is true then require transferFrom and transferFromDate as well
    const isExternal = this.hardwareForm.get('external')?.value;
    const transferFieldsValid = isExternal ? (controls['transferFrom'].value && controls['transferFromDate'].value && controls['transferTo'].value && controls['transferToDate'].value) : true;

    const purchaseCost = this.hardwareForm.get('purchaseCost')?.value;
    if(purchaseCost && purchaseCost.toString().trim() !== '') {
      return basicFieldsValid && transferFieldsValid && !!controls['currency'].value;
    } else {
      return basicFieldsValid && transferFieldsValid;
    }
  }
}
