import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { MessageService } from 'primeng/api';

@Injectable({
  providedIn: 'root'
})
export class ActivatedRouterService {

  constructor(private router: Router) { }

  updateError(err: any, messageService: MessageService) {
    console.error('API Error:', err);  
    switch (err?.status) {
      case 400: // Bad Request (Validation Errors)
        if (err?.error?.error) {
          // err.error.messages.forEach((msg: string) => {
            messageService.add({ severity: 'error', summary: 'Validation Error', detail: err?.error?.error });
          // });
        } else {
          console.error('API Error:', err?.error);  
          messageService.add({ severity: 'error', summary: 'Validation Error', detail: err?.error?.message || err?.error?.non_field_errors || err?.error?.errors?.[0]?.non_field_errors?.[0]  || err?.error?.[0]?.non_field_errors?.[0] || err?.[0] || 'Invalid request' });
        }
        break;
  
      // case 401: // Unauthorized
      //   setTimeout(() => {
      //     localStorage.clear();
      //     this.router.navigate(['/login']);
      //   }, 1500);
      //   messageService.add({ severity: 'error', summary: 'Unauthorized', detail: 'Session expired. Please login again.' });
      //   break;
  
      case 403: // Forbidden
        messageService.add({ severity: 'error', summary: 'Forbidden', detail: 'You do not have permission to perform this action.' });
        break;
  
      case 404: // Not Found
      if (err?.error?.messages instanceof Array) {
        err.error.messages.forEach((msg: string) => {
          messageService.add({ severity: 'error', summary: 'Not Found', detail: msg });
        });
      } else {
        messageService.add({ severity: 'error', summary: 'Not Found', detail: err?.error?.message || 'The request not found' });
      }
      break;
      case 500: // Internal Server Error
        messageService.add({ severity: 'error', summary: 'Server Error', detail: 'An unexpected error occurred. Please try again later.' });
        break;
  
      case 502: // Bad Gateway
        messageService.add({ severity: 'error', summary: 'Server Down', detail: 'The server is temporarily unavailable. Please try again later.' });
        break; 
  
      default: // Other Unknown Errors
        messageService.add({
          severity: 'error',
          summary: 'Unexpected Error',
          detail: err?.error?.message || err?.error?.error || 'An unknown error occurred. Please contact support.'
        });
    }
  }

  // decodeJWT(token:string) {
  //   // Split the JWT token into its three parts (Header, Payload, Signature)
  //   const [header, payload, signature] = token.split('.');
  
  //   // Decode base64url encoded parts
  //   const decodedHeader = JSON.parse(atob(header.replace(/-/g, '+').replace(/_/g, '/')));
  //   const decodedPayload = JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')));
  
  //   return {
  //     header: decodedHeader,
  //     payload: decodedPayload,
  //     signature: signature
  //   };
  // }
}
