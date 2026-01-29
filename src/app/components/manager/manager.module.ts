import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { TooltipModule } from 'primeng/tooltip';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { ToastModule } from 'primeng/toast';
import { DialogModule } from 'primeng/dialog';
import { ConfirmDialogModule } from 'primeng/confirmdialog';

import { ManagerRoutingModule } from './manager-routing.module';


@NgModule({ declarations: [
  ], imports: [CommonModule,
       ManagerRoutingModule,
        ReactiveFormsModule,
        TooltipModule,
        FormsModule,
        ToastModule,
        DialogModule,
        ConfirmDialogModule], providers: [provideHttpClient(withInterceptorsFromDi())] })
export class ManagerModule { }
