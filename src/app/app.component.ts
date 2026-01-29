import { LoaderComponent } from './loader/loader.component';
import { Component, DestroyRef, inject, Injectable, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Title } from '@angular/platform-browser';
import { ActivatedRoute, NavigationEnd, Router, RouterOutlet } from '@angular/router';
import { delay, filter, map, tap } from 'rxjs/operators';
import { ScrollingModule } from '@angular/cdk/scrolling';
import { Dialog, DialogModule } from 'primeng/dialog';
import { SessionExpiredService } from './services/session-expired-service';
import { LoginComponent } from './components/login/login.component';
import { MessageService } from 'primeng/api';


@Component({
    selector: 'app-root',
    imports: [RouterOutlet, LoaderComponent,ScrollingModule, DialogModule],
    templateUrl: './app.component.html',
    styleUrls: ['./app.component.scss'],
    standalone:true
})
export class AppComponent implements OnInit {
  title = 'Roboxa Project Management Application';
  isLoading:boolean= false;
  showSessionDialog = false;
  showResumeDialog = false;

  readonly destroyRef: DestroyRef = inject(DestroyRef);
  readonly activatedRoute: ActivatedRoute = inject(ActivatedRoute);
  readonly router = inject(Router);
  readonly titleService = inject(Title);
  sessionExpiredService = inject(SessionExpiredService);
  messageService = inject(MessageService)


  constructor( private loginComponent : LoginComponent) {
    this.titleService.setTitle(this.title);
  }
  
  ngOnInit(): void {
    // const token = localStorage.getItem('access_token');
    // const refreshToken = localStorage.getItem('refresh_token');
    // if (token && refreshToken) {
    //   //if an user is logged in an tab and trying to open application in other tab, then
    //   //by default same user will be logged in that tab also
    //   this.loginComponent.navigateToRoleBasedRoute();
    // } else {
    //   console.log('no token available from app component');
    //   localStorage.clear();
    //   this.router.navigate(['/login']);
    // }

    this.router.events.pipe(
        takeUntilDestroyed(this.destroyRef)
      ).subscribe((evt) => {
      if (!(evt instanceof NavigationEnd)) {
        return;
      }
    });

    this.sessionExpiredService.showDialog$.subscribe(show => {
      this.showSessionDialog = show;
    });

     this.sessionExpiredService.refreshFailed$.subscribe(() => {
        this.showSessionDialog = false;
        this.showResumeDialog = true;
    });
  }

  onSessionConfirm() {
    this.sessionExpiredService.confirm();
  }

  onSessionCancel() {
    localStorage.clear();
    this.router.navigate(['/login']);
    this.sessionExpiredService.close();
  }

  onClose() {
    this.showResumeDialog = false;
    localStorage.clear();
    this.router.navigate(['/login']);
  }

}
