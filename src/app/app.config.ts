import { ApplicationConfig, importProvidersFrom } from '@angular/core';
import {
  provideRouter,
  RouterModule,
  withEnabledBlockingInitialNavigation,
  withHashLocation,
  withInMemoryScrolling,
  withRouterConfig,
} from '@angular/router';


import { routes } from './app.routes';
import { BrowserAnimationsModule, provideAnimations } from '@angular/platform-browser/animations';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { tokenInterceptor} from './services/token.interceptor';
import { MessageService } from 'primeng/api';
import { MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatToolbarModule } from '@angular/material/toolbar';
import { AuthGuard } from './services/auth.guard';
import { LoginService } from './services/login.service';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes,
      withRouterConfig({
        onSameUrlNavigation: 'reload'
      }),
      withInMemoryScrolling({
        scrollPositionRestoration: 'top',
        anchorScrolling: 'enabled'
      }),
      withEnabledBlockingInitialNavigation(),
    ),
    provideHttpClient(withInterceptors([tokenInterceptor])),
    importProvidersFrom(
      MatSidenavModule,
      MatToolbarModule,
      MatButtonModule,
      MatDialogModule,
      BrowserAnimationsModule,
      RouterModule
    ),
    provideHttpClient(),
    MessageService,
    AuthGuard, // Ensure this is correctly provided
    LoginService
  ],
}