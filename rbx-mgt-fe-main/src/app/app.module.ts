import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { MaterialModule } from './material-module';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { HTTP_INTERCEPTORS, HttpClientModule } from '@angular/common/http';
import { LoginComponent } from './components/login/login.component';
import { ForgotPasswordComponent } from './components/forgot-password/forgot-password.component';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { MessageService } from 'primeng/api';
import { ToastModule } from 'primeng/toast';
import { ScrollingModule } from '@angular/cdk/scrolling';

@NgModule({
  declarations: [
  ],
  
  imports: [
    BrowserModule,
   // AppRoutingModule,
    BrowserAnimationsModule,
    MaterialModule,
    ReactiveFormsModule,
    FormsModule,
    CommonModule,
    HttpClientModule,
    RouterLink,
    ToastModule,
    ScrollingModule
  ],
  providers: [
   
  ],
  bootstrap: [
    // AppComponent
  ]
})
export class AppModule { }
