import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { HttpRequest, HttpHandlerFn, HttpEvent, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, finalize } from 'rxjs/operators';
import { LoginService} from '../services/login.service';
import { SessionExpiredService } from './session-expired-service';

export const tokenInterceptor: HttpInterceptorFn = (req: HttpRequest<any>, next: HttpHandlerFn): Observable<HttpEvent<any>> => {
  const router = inject(Router);
  const loaderService = inject(LoginService);
  const sessionExpiredService = inject(SessionExpiredService);


  const token = localStorage.getItem('access_token');
  const excludedUrls = [
      '/login/', '/forgot-password/', '/change_password/' ,'/dropdown-data.json'
  ];
  const isExcluded = excludedUrls.some(url => req.url.includes(url));
  let isRefreshing = false;

  loaderService.showLoader(); // Show loader immediately

  if (isExcluded) {
      return next(req).pipe(
        finalize(() => {
          loaderService.hideLoader();
        })
      );
  }

  const cloneReq = req.clone({
    setHeaders: {
      Authorization: `Bearer ${token}`
    }
  });
  
  return next(cloneReq)
  .pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 401 && !req.url.includes('/refresh_token/')) {
        if (!isRefreshing) {
          isRefreshing = true;

          const token = localStorage.getItem('access_token');
          const refreshToken = localStorage.getItem('refresh_token');
          if (token && refreshToken) {
            sessionExpiredService.open(() => {
              loaderService.$refreshToken.next(true);
            });
          } else {
            console.log('no token available from token interceptor');
            localStorage.clear();
            router.navigate(['/login']);
          }
        }
      }

      // if (error.status === 401) {
      //   sessionExpiredService.open(() => {
      //     loaderService.$refreshToken.next(true);
      //   });
      // }
      return throwError(() => error);
    }),
    finalize(() => {
      loaderService.hideLoader()
    }),
  );
};
