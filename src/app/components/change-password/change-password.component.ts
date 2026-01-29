import { Component, signal } from '@angular/core';
import { FormBuilder, FormControl, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import {passwordCheck, passwordValidator} from '../../validators/password'
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import {MessageService } from 'primeng/api'
import { LoginService } from '../../services/login.service';
import { ToastModule } from 'primeng/toast';
import { ActivatedRouterService } from '../../services/activated-router-service';
import { NoSpaceDirective} from 'src/app/directives/no-space.directive';
import { MinMaxValidatorDirective } from 'src/app/directives/min-max-validator.directive';

@Component({
  selector: 'app-change-password',
  imports: [CommonModule, FormsModule, ReactiveFormsModule, ToastModule,NoSpaceDirective,MinMaxValidatorDirective],
  standalone:true,
  templateUrl: './change-password.component.html',
  styleUrls: ['./change-password.component.scss']
})
export class ChangePasswordComponent {

  constructor(
    private formBuilder: FormBuilder,
    private router:Router,
    private loginService:LoginService,
    private messageService:MessageService,
    private activatedRouterService: ActivatedRouterService
  ) {}

  forgetForm!: FormGroup;
  showPassword:boolean = false;
  showConfirmPassword:boolean = false;


  ngOnInit() {
    const username = localStorage.getItem('email');
    this.forgetForm = this.formBuilder.group({
      username: [username, [Validators.required, Validators.minLength(6),Validators.maxLength(100), Validators.email]],
      new_password: ['', [Validators.required, passwordValidator()]],
      confirm_password: ['', Validators.required],
    },
      {
        validators: passwordCheck('new_password', 'confirm_password')
      })
  }

  togglePasswordVisibility(){
    this.showPassword=!this.showPassword
  }

  showConfirmPasswordField(){
    this.showConfirmPassword=!this.showConfirmPassword
  }
  
  preventPaste(event:any) {
    event.preventDefault();
  }

  getFormControl(formControlName:string) {
    return this.forgetForm.get(formControlName);
  }

  onSubmit() {
    this.loginService.showLoader();
    this.messageService.clear()
    const obj = {
      email: this.forgetForm.controls['username'].value,
      new_password:this.forgetForm.controls['confirm_password'].value
    }
      this.loginService.changePassword(obj).subscribe(res => {              
        this.messageService.add({ severity: 'success', summary: '', detail: 'Password changed successfully' });
          setTimeout(() => {
            localStorage.clear();
            this.loginService.hideLoader();
            this.router.navigate(['login']);
          }, 500)
        },(err: any) => {  
          this.loginService.hideLoader();
          this.activatedRouterService.updateError(err, this.messageService)
        }
      )
    }
}