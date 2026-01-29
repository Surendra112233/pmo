// session-expired.service.ts
import { inject, Injectable } from '@angular/core';
import { BehaviorSubject, Subject } from 'rxjs';
import { environment } from '../../environment';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { AppComponent } from '../app.component';
import { MessageService } from 'primeng/api';

@Injectable({
  providedIn: 'root'
})

export class SessionExpiredService {
  http = inject(HttpClient);
  private router = inject(Router);

  private readonly url = environment.apiUrl;
  private showDialogSubject = new BehaviorSubject<boolean>(false);
  showDialog$ = this.showDialogSubject.asObservable();

  refreshFailedSubject = new Subject<void>();
  refreshFailed$ = this.refreshFailedSubject.asObservable();

  notifyRefreshFailed() {
    this.refreshFailedSubject.next();
  }

  private onConfirmCallback: (() => void) | null = null;

  open(onConfirm: () => void) {
    this.onConfirmCallback = onConfirm;
    this.showDialogSubject.next(true);
  }

  confirm() {
    if (this.onConfirmCallback) this.onConfirmCallback();
    this.close();
  }

  close() {
    this.showDialogSubject.next(false);
    this.onConfirmCallback = null;
    // if (this.shouldRefreshRoute) {
    //   setTimeout(() => {
    //     const currentRoute = this.router.url;
    //     this.router.navigateByUrl('/', { skipLocationChange: true }).then(() => {
    //       this.router.navigateByUrl(currentRoute);
    //     });
    //   }, 1000);
    // } else {
    //   localStorage.clear()
    //   this.router.navigate(['/login']);
    // }
  }

  getRefreshToken() {
    const obj = {
        email: localStorage.getItem('user_mail'),
        refresh_token:	localStorage.getItem('refresh_token'),
    }
    // console.log('refresh token call:::::', obj)
    this.http.post(this.url+'login/refersh_token/',obj)
    .subscribe((res:any) => {
        if (res) {
            localStorage.setItem('access_token', res.access_token);
            localStorage.setItem('refresh_token', res.refresh_token);
            localStorage.setItem('Roles',res.roles && res.roles[0] ? res.roles[0].join(",") : "");
            localStorage.setItem('user_name',res.user_name);
            localStorage.setItem('designation',res.designation);
            const loggedUserDetails=this.decodeJWT(res.access_token);
            localStorage.setItem("userId",loggedUserDetails.payload?.user_id);

            setTimeout(() => {
              const currentRoute = this.router.url;
              this.router.navigateByUrl('/', { skipLocationChange: true }).then(() => {
                this.router.navigateByUrl(currentRoute);
              });
            }, 1000);
        }
      }, err=> {
        //  if (err.status === 400 && err.error?.error?.includes("Invalid or expired refresh token.")) {
          //if token expired error occurs even after hitting refresh token api then execute logic
          this.notifyRefreshFailed();
        // }
             
      })
    }

    decodeJWT(token:string) {
    // Split the JWT token into its three parts (Header, Payload, Signature)
    const [header, payload, signature] = token.split('.');
  
    // Decode base64url encoded parts
    const decodedHeader = JSON.parse(atob(header.replace(/-/g, '+').replace(/_/g, '/')));
    const decodedPayload = JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')));
  
    return {
      header: decodedHeader,
      payload: decodedPayload,
      signature: signature
    };
  }
}