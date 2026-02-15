import { Component, inject, signal, ElementRef, ViewChild, OnInit, Injectable } from '@angular/core';
import { FormBuilder, FormControl, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api'
import { ActivatedRouterService } from 'src/app/services/activated-router-service';
import { LoginService } from 'src/app/services/login.service';
import { CommonModule } from '@angular/common';
import { NoSpaceDirective} from 'src/app/directives/no-space.directive';
// import { CookieService } from 'ngx-cookie-service';

@Injectable({
  providedIn: 'root'
})

@Component({
  selector: 'app-login',
  imports: [FormsModule, CommonModule, ReactiveFormsModule, RouterLink, ToastModule,NoSpaceDirective],
  standalone:true,
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss'],
  // providers: [CookieService]
})
export class LoginComponent implements OnInit{
    remainingTime: number = 60; // Timer duration in seconds
    min:string | number='01';
    sec:string | number='00';
    isResendDisabled: boolean = true; // Disable the resend button initially
    isLoginbtnDisable:boolean=false;
    private timerInterval: any; // Holds the interval reference
    otpText:boolean=true;
    validateOtp: string | null = null; 
    apiErrors: { [key: string]: string } = {};
    loginErrorMessage:string='';
    emailDomain = '@roboxaservices.com';
    domainAdded = false;
    isMobile: boolean = false;

    @ViewChild('usernameField') usernameField!: ElementRef;
    @ViewChild('passwordField') passwordField!: ElementRef;
  
    
    constructor(
      private formBuilder: FormBuilder,
      private messageService: MessageService,
      private loginService: LoginService,
      private activatedRouterService: ActivatedRouterService,
      // private cookieService: CookieService
    ){}
  
    showPassword:boolean = false;
    enableOTPField:boolean = false;
    loginForm!: FormGroup;
    router = inject(Router)
  
    ngOnInit(): void {
      /* CHANGE START: Detect mobile device & apply dynamic layout */
      const userAgent = navigator.userAgent.toLowerCase();
      console.log(userAgent)

      this.isMobile = /android|iphone|ipad|ipod/.test(userAgent);

      if (this.isMobile) {
        document.body.classList.add('mobile-login');
      } else {
        document.body.classList.remove('mobile-login');
      }
      /* CHANGE END */

      this.loginForm = this.formBuilder.group({
        username: new FormControl('', [Validators.required, Validators.minLength(6),Validators.maxLength(100), Validators.email]),
        password: new FormControl('', [Validators.required,Validators.minLength(6),Validators.maxLength(16)]),
        otp: new FormControl('', [Validators.required]),
        rememberMe: new FormControl(false)
      });

      this.loadRememberedCredentials();
    }

    loadRememberedCredentials(): void {
      const savedUsername = this.getCookie('username');
      const savedPassword = this.getCookie('password');

      if (savedUsername && savedPassword) {
        this.loginForm.patchValue({ 
          username : savedUsername, 
          password : savedPassword,
          rememberMe: true,
        });
      }
    }
  
    clearError(){
      this.apiErrors['errMsg']='';
      this.apiErrors['username']='';
      this.apiErrors['password']='';
      this.loginErrorMessage = '';
    }

    handleEmailKeyDown(event: KeyboardEvent) {
      if (event.key === '@' && !this.domainAdded) {
        event.preventDefault(); // prevent default "@" input
        const ctrl = this.loginForm.get('username');
        const currentValue = ctrl?.value || '';
        // Append domain
        ctrl?.setValue(currentValue + this.emailDomain);
        this.domainAdded = true;
      }
    }
       
    onEmailInput() {
      const ctrl = this.loginForm.get('username');
      const value = ctrl?.value || '';
      // Reset the domainAdded flag if user clears or edits the domain
      this.domainAdded = value.includes(this.emailDomain);
      }
  
    togglePasswordVisibility(){
      this.showPassword= !this.showPassword
    }
    preventPaste(event:any) {
      event.preventDefault();
    }
  
    getFormControl(formControlName:string) {
      return this.loginForm.get(formControlName);
    }
  
    getFormValidation() {
      return this.loginForm.controls['username'].status === 'VALID' && this.loginForm.controls['password'].status === 'VALID'
    }
  
    startTimer(timeRemains:number): void {
      let timeLeft = 60; // Total time in seconds for 1 minute
      this.isResendDisabled = true; 
      this.timerInterval = setInterval(() => {
        this.otpText=true;
        var m = Math.floor(timeRemains / 60);
        var s = timeRemains % 60;
        this.min  = m < 10 ? '0' + m : m;
        this.sec = s < 10 ? '0' + s : s;
        if (timeRemains <= 0) {
          clearInterval(this.timerInterval); // Stop the timer
          this.isResendDisabled = false; // Enable the Resend OTP button
          this.otpText=false
          // this.validateOtp='';
          this.getFormControl('otp')?.reset(); 
        }
        timeRemains--;
      }, 1000);
    }
  
    validateOTP(event:any, type:any) {
      let inputValue = event.target.value.trim();   
      // Remove non-numeric characters
      let numericValue = inputValue.replace(/\D/g, ''); 
      if(type ==='otp'){
        if (numericValue.length > 6) {
            numericValue = numericValue.slice(0, 6);
        }
      }
      event.target.value = numericValue;
    }
  
    otp() {
      this.isResendDisabled=true
      this.onLogin(true)
    }
  
    focusErrorFields() {
      if (this.apiErrors['errMsg']) {
        this.usernameField.nativeElement.focus();
        // setTimeout(() => {
          this.passwordField.nativeElement.focus();
        // }, 100); // Add slight delay to focus both fields sequentially
        return;
      }  
      if (this.apiErrors['username']) {
        this.usernameField.nativeElement.focus();
      }
      if (this.apiErrors['password']) {
        this.passwordField.nativeElement.focus();
      }
    }
  
    resendOtp(): void {
      this.apiErrors = {}; // Clear error object to reset the error state
      // Request to resend OTP
      const obj = {
        email: this.loginForm.controls['username'].value
      };
    
      this.loginService.resendOtpToMail(obj).subscribe(
        (res: any) => {
        //  console.log("OTP resent:", res.otp);
          // this.validateOtp = res.otp; // Set the validateOtp value
          this.getFormControl('otp')?.reset(); 
          this.messageService.add({
            severity: 'success',
            summary: '',
            detail: 'Please enter OTP sent to your registered email'
          });  
          this.startTimer(60);  // Restart the countdown timer
        },
        (err: any) => {
          this.getFormControl('otp')?.reset(); 
          // Handle error from API and update the error messages
          this.activatedRouterService.updateError(err, this.messageService);
        }
      );
    }
    
  sendOtp(): void {
    this.isLoginbtnDisable=true;
    const obj = {
      email: this.loginForm.controls['username'].value
    };
    this.loginService.sendOtpToMail(obj).subscribe(
      (res: any) => {
        // this.loginService.showLoader();
        // console.log("OTP sent:", res.otp);
        // this.validateOtp = res.otp;  // Convert OTP to number
        this.startTimer(60);
        this.enableOTPField = true;
        this.isResendDisabled = true;
        this.messageService.add({ severity: 'success', summary: '', detail: 'Please enter OTP sent to your registered email' });     
      },
      (err: any) => {
        this.isLoginbtnDisable=false;
        this.loginService.hideLoader();
        this.activatedRouterService.updateError(err, this.messageService);
      }
    );
  }
  
  loginApi(){
    const loginObj = {
      email: this.loginForm.controls['username'].value,
      password: this.loginForm.controls['password'].value,
      otp: this.loginForm.controls['otp'].value
    }
    this.loginService.userLogin(loginObj).subscribe(res => {     
      this.messageService.add({
        severity: 'success',
        summary: '',
        detail: 'Logging in. Please wait...'
      }); 
      // Navigate to the desired route
      this.navigateToRoleBasedRoute();
      // this.router.navigate(['/um/maintain_users']);
    },(err: any) => {
      if (err.error.error) {
        let msg = err.error.error;
        if(msg === "Invalid Email Format.") {
          this.apiErrors['username'] = msg;
        } else if (msg === "Password must contain at least one special character and one digit.") {
          this.apiErrors['password'] = msg;
        } else if (msg === "Invalid credentials.") {
          this.apiErrors['errMsg'] = msg;
        }
        else if (msg === "Invalid email or password") {
          this.apiErrors['errMsg'] = msg;
        }
        else {
          const errMsg = err?.error?.error || err?.error
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: errMsg
          });
          // if (err && err.status === 401) { 
          //   this.messageService.add({
          //     severity: 'error',
          //     summary: 'Unauthorized',
          //     detail: 'You are not authorized to perform this action. Please log in again.'
          //   });
          // } else if (err && err.status === 400) { 
          //   this.messageService.add({
          //     severity: 'error',
          //     summary: 'Bad Request',
          //     detail: 'Please enter a valid OTP'
          //   });
          // } else { 
          //   this.messageService.add({
          //     severity: 'error',
          //     summary: 'Error',
          //     detail: 'An unexpected error occurred. Please try again or contact Roboxa-IT Service.'
          //   });
          // }
        }
      }
       else if(err.error.email instanceof Array) 
        {
        let errMessages = err.error.email;
        errMessages.forEach((msg:string) => {
          if(msg === "Enter a valid email address.") {
            this.apiErrors['username']  = msg;
          } else if (msg === "Password must contain at least one special character and one digit.") {
            this.apiErrors['password'] = msg;
          }
        })  
        }
      this.focusErrorFields(); 
    }
  )
  }
  
    onLogin(isResend:boolean) {
       const formValues = this.loginForm.value;

      if (formValues.rememberMe) {
        // Set cookies for username and password if "Remember Me" is checked
        this.setCookie('username', formValues.username, 30); // Expires in 30 days
        this.setCookie('password', formValues.password, 30); // Expires in 30 days
      } else {
        // Remove cookies if "Remember Me" is unchecked
        this.deleteCookie('username');
        this.deleteCookie('password');
      }

      this.apiErrors = {}; // Reset API errors    
      this.messageService.clear();
      this.loginService.showLoader();
      const obj = {
        email: this.loginForm.controls['username'].value,
        password:this.loginForm.controls['password'].value
      };
      
      this.loginService.loginJWTToken(obj).subscribe(        
        (res: any) => {
          if(res.user.change_password_required == true) {
            localStorage.setItem('email', res.user.email);
             setTimeout(() => {
              this.router.navigate(['/change_password']);
            }, 1000);
          } else {
            if(res.message=="Login successful!"){
              setTimeout(() => {
                localStorage.setItem('user_mail', res.user.email);
                // localStorage.setItem('user_id', res.user.id);
                this.sendOtp();  
              },50)
            }
          }

        },
        (err: any) => {
         this.loginService.hideLoader();
         console.log(err) 
          this.loginErrorMessage=err?.error?.error?.[0] || err?.error?.non_field_errors || err?.error?.email?.[0]; 
        }
      );
    }
  
    onSubmit(): void {
      this.messageService.clear();
      const email = this.loginForm.controls['username'].value;
      const otp = this.loginForm.controls['otp'].value;
  
    // Check if OTP is empty or invalid
    if (!otp || otp.trim() === '') {
      this.messageService.add({
        severity: 'error',
        summary: '',
        detail: 'Please enter a valid OTP'
      });
      return; 
    }
  
    // if (this.validateOtp === null || this.validateOtp === undefined) {
    //   this.messageService.add({
    //     severity: 'error',
    //     summary: '',
    //     detail: 'OTP validation error: OTP is not set properly.'
    //   });
    //   return; 
    // }
  
    // Validate OTP
    // if (otp == this.validateOtp) { 
      this.loginApi();
      //console.log("Login success... OTP validated");   
    // } else {
    //   this.messageService.add({
    //     severity: 'error',
    //     summary: '',
    //     detail: 'Invalid OTP. Please try again.'
    //   });
    // }
    }
    
    navigateToRoleBasedRoute(): void {
      // Retrieve roles from localStorage if needed
      const storedRoles = localStorage.getItem('Roles');
      // const roleArray = storedRoles ? storedRoles.split(',').map(role => role.toUpperCase()) : [];
      const roleArray = storedRoles 
      ? storedRoles.split(',').map(role => role.trim().toUpperCase().replace(/\s+/g, '')) 
      : [];
      
      // Convert the role conditions to uppercase for case-insensitive comparison
      if (roleArray.includes('USERADMIN')) {
        this.router.navigate(['/um/maintain_users']);
      } else if (roleArray.includes('DATAADMIN')) {
        this.router.navigate(['/md/project_tasks']);
      } else if (roleArray.includes('PMO')) {
        this.router.navigate(['/pmo/project-assignment']);
      } else if (roleArray.includes('MANAGER')) {
        this.router.navigate(['/manager/mng-dashboard']);
        // this.router.navigate(['/manager/approval']);
      } else if (roleArray.includes('EMPLOYEE')) {
        this.router.navigate(['/emp/emp-dashboard']);
      }  else if (roleArray.includes('HR')) {
        this.router.navigate(['/hr/employees']);
      }  else if (roleArray.includes('DELIVERYHEAD')) {
        this.router.navigate(['/dh/dh-dashboard']);
        // this.router.navigate(['/dh/dh-approval']);
      } else if (roleArray.includes('MANAGEMENT')) {
        this.router.navigate(['/mgmnt/mnt-dashboard']);
        // this.router.navigate(['/mgmnt/mnt-approval']);
      } else {
        this.router.navigate(['/access-denied']);
      }
    }
    
    // -------------------
    // Cookie utilities
    // -------------------

    setCookie(name: string, value: string, days: number) {
      const expires = new Date(Date.now() + days * 864e5).toUTCString();
      document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/`;
    }

    getCookie(name: string): string {
      const cookie = document.cookie
        .split('; ')
        .find(row => row.startsWith(name + '='));
      return cookie ? decodeURIComponent(cookie.split('=')[1]) : '';
    }

    deleteCookie(name: string) {
      document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/`;
    }

}
