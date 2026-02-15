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
import { AlphanumericDirective } from 'src/app/directives/alphanumeric.directive';

@Component({
  selector: 'app-forgot-password',
  imports: [CommonModule, FormsModule, ReactiveFormsModule, ToastModule,NoSpaceDirective,MinMaxValidatorDirective,
    AlphanumericDirective],
  standalone:true,
  templateUrl: './forgot-password.component.html',
  styleUrls: ['./forgot-password.component.scss']
})
export class ForgotPasswordComponent {

  constructor(
    private formBuilder: FormBuilder,
    private router:Router,
    private loginService:LoginService,
    private messageService:MessageService,
    private activatedRouterService: ActivatedRouterService
  ) {}

  forgetForm!: FormGroup;
  enablePasswordField:boolean = false;
  enableOTPField:boolean = false;
  showPassword:boolean = false;
  showConfirmPassword:boolean = false;
  remainingTime: number = 60; // Timer duration in seconds
  min:string | number='01';
  sec:string | number='00';
  isResendDisabled: boolean = true; // Disable the resend button initially
  private timerInterval: any; // Holds the interval reference
  otpText:boolean=true;
//  otpValue:number=0;
//  oldOtp:number=0;
  emailDomain = '@roboxaservices.com';
  domainAdded = false;

  ngOnInit() {
    this.forgetForm = this.formBuilder.group({
      username: ['', [Validators.required, Validators.minLength(6),Validators.maxLength(100), Validators.email]],
      otp: [''],
      new_password: ['', [Validators.required, passwordValidator()]],
      confirm_password: ['', Validators.required],
    },
      {
        validators: passwordCheck('new_password', 'confirm_password')
      })
  }

  handleEmailKeyDown(event: KeyboardEvent) {
    if (event.key === '@' && !this.domainAdded) {
      event.preventDefault(); // prevent default "@" input
      const ctrl = this.forgetForm.get('username');
      const currentValue = ctrl?.value || '';
      // Append domain
      ctrl?.setValue(currentValue + this.emailDomain);
      this.domainAdded = true;
    }
  }

  onEmailInput() {
    const ctrl = this.forgetForm.get('username');
    const value = ctrl?.value || '';
    // Reset the domainAdded flag if user clears or edits the domain
    this.domainAdded = value.includes(this.emailDomain);
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

  startTimer(timeRemains:number): void {
    let timeLeft = 60; // Total time in seconds for 1 minute
    this.timerInterval = setInterval(() => {
      this.otpText=true
      var m = Math.floor(timeRemains / 60);
      var s = timeRemains % 60;
      this.min  = m < 10 ? '0' + m : m;
      this.sec = s < 10 ? '0' + s : s;
      if (timeRemains <= 0) {
        clearInterval(this.timerInterval); // Stop the timer
        this.isResendDisabled = false; // Enable the Resend OTP button
        this.otpText=false
      }
      timeRemains--;
    }, 1000);
  }

  otp() {
    // this.oldOtp=this.otpValue;
    this.isResendDisabled = true;
    this.forgetForm.controls['otp'].setValue('');
    this.sendOTP();
  }

  sendOTP() {
    this.loginService.showLoader();
    const email = this.forgetForm.controls['username'].value;
      this.loginService.sendOtpToMail({email: email}).subscribe(res => {
        // this.otpValue=res?.otp;
        this.loginService.hideLoader();
        this.messageService.add({ severity: 'success', summary: '', detail: 'Please enter OTP sent to your registered email' });
        this.startTimer(60)        
        setTimeout(() => {
          this.enableOTPField = true;
          this.enablePasswordField = false;
        }, 500)
        },(err: any) => {
        this.loginService.hideLoader();
        const errMsg = err?.error?.error;
        this.messageService.add({ severity: 'error', summary: '', detail: errMsg });
          // this.activatedRouterService.updateError(err, this.messageService)
        }
      )
    }

  validateOTP() {
    this.loginService.showLoader();
    // if(this.otpValue === +this.forgetForm.controls['otp'].value){
    //   this.messageService.add({ severity: 'success', summary: '', detail: 'OTP validation successful. Please enter password' });
    //     setTimeout(() => {
    //       this.enableOTPField = false;
    //       this.enablePasswordField = true;
    //       }, 500);
    // }
    // else if(this.oldOtp===+this.forgetForm.controls['otp'].value){
    //   this.messageService.add({ severity: 'error', summary: '', detail: 'OTP Expired' });
    // }
    // else{
    //   this.messageService.add({ severity: 'error', summary: '', detail: 'Please Enter Valid OTP' });
    //   this.enableOTPField = true;
    //    this.enablePasswordField = false;
    // }

      const obj = {
        email: this.forgetForm.controls['username'].value,
        otp: this.forgetForm.controls['otp'].value
      }
      this.loginService.verifyOTP(obj).subscribe(res => {
        this.messageService.add({ severity: 'success', summary: '', detail: 'OTP validation successful. Please enter password' });
        setTimeout(() => {
          this.enableOTPField = false;
          this.enablePasswordField = true;
          }, 500)
        },(err: any) => {    
          this.activatedRouterService.updateError(err, this.messageService)
        }
      )
      this.loginService.hideLoader();
  }

  onSubmit() {
    this.loginService.showLoader();
    this.messageService.clear()
    const obj = {
      email: this.forgetForm.controls['username'].value,
      confirm_password:this.forgetForm.controls['confirm_password'].value
    }
      this.loginService.forgotPassword(obj).subscribe(res => {              
        this.messageService.add({ severity: 'success', summary: '', detail: 'Password changed successfully' });
          setTimeout(() => {
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
