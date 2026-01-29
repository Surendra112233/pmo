import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
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
  selector: 'app-add-status',
  templateUrl: './add-status.component.html',
  styleUrls: ['./add-status.component.scss'],
  imports: [ReactiveFormsModule, CommonModule, DropdownModule, AlphaNumericSpecialCharsDirective]
})
export class AddStatusComponent {
  @Input() from_hardware: boolean = false; // default behavior
  @Input() from_software: boolean = false; // default behavior

  @Output() status_for_hardware = new EventEmitter<any>(); // for dialog usage
  @Output() status_for_software = new EventEmitter<any>(); // for dialog usage

  statusForm!: FormGroup;
  status_id:string = '';
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
    this.buildStatusForm();

    this.activatedRoute.paramMap.subscribe(params => {
      this.status_id = params.get('id') || '';

      if(this.from_hardware || this.from_software) {
        this.btn_text='Save';
        this.page_title='Add';
      } else {
        if(this.status_id){
          this.getStatusDetails();
          this.btn_text='Update';
          this.page_title='Edit';
        } else{
          this.btn_text='Save';
          this.page_title='Add';
        }
      }
      
    });
  }
  
  buildStatusForm() {
    this.statusForm = this.fb.group({
      status_code: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(15)]],
      status_name: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(40)]]
    });
  }

  getStatusDetails() {
    this.masterDataService.getStatusById(this.status_id).subscribe((res: any) => {
      let data = res['data'];

      // patch main fields
      this.statusForm.patchValue({
        status_code: data.status_code,
        status_name: data.status_name
      });
    },(err: any) => { 
      this.activatedRouterService.updateError(err, this.messageService)
    })
  }

  onSubmit() {
    if (this.statusForm.valid) {
      const formValue = { ...this.statusForm.value };
      console.log('Final payload:', formValue);

      if (this.status_id && !this.from_hardware && !this.from_software) {
        // call update API
        this.masterDataService.updateStatus(this.status_id, formValue).subscribe( data => {
          this.messageService.add({ severity: 'success', summary: '', detail: 'Status updated successfully' });
          setTimeout(() => {
              this.router.navigate(['/md/status']);
          }, 1000);        
        },(err: any) => {
          this.activatedRouterService.updateError(err, this.messageService);      
        });
      } else {
        // call create API
        this.masterDataService.addStatus(formValue).subscribe(data => {
          this.messageService.add({ severity: 'success', summary: '', detail: 'Status added successfully' });
          if(this.from_hardware) {
            this.status_for_hardware.emit(formValue);
          } else if (this.from_software) {
            this.status_for_software.emit(formValue);
          } else {
            setTimeout(() => {
              this.router.navigate(['/md/status']);;
            }, 1000);            
          }
        
        },(err: any) => {
          this.activatedRouterService.updateError(err, this.messageService);      
        });
      }
    } else {
      this.statusForm.markAllAsTouched();
    }
  }

  onCancel() {
    this.statusForm.reset();
    if(this.from_hardware) {
      this.status_for_hardware.emit(null);
    } else if (this.from_software) {
      this.status_for_software.emit(null);
    } else {
      this.router.navigate(['/md/status']);
    }
  }
}
