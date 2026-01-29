import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { TooltipModule } from 'primeng/tooltip';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { ToastModule } from 'primeng/toast';
import { DialogModule } from 'primeng/dialog';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { TravelRequestComponent } from './travel-request/travel-request.component';
import { TravelRoutingModule } from './travel-routing.module';
import { RaiseTravelRequestComponent } from './raise-travel-request/raise-travel-request.component';
import { RequestsListComponent } from './requests-list/requests-list.component';
import { ViewTravelRequestComponent } from './view-travel-request/view-travel-request.component';
import { EditTravelRequestComponent } from './edit-travel-request/edit-travel-request.component';
import { RaiseCashAdvanceRequestComponent } from './raise-cash-advance-request/raise-cash-advance-request.component';
import { CashAdvanceRequestsListComponent } from './cash-advance-requests-list/cash-advance-requests-list.component';



@NgModule({
  declarations: [
  
  ],
  imports: [
    CommonModule,
    TravelRoutingModule,
    TravelRequestComponent,
    RequestsListComponent,
    ViewTravelRequestComponent,
    EditTravelRequestComponent,
    RaiseTravelRequestComponent, 
    RaiseCashAdvanceRequestComponent,
    CashAdvanceRequestsListComponent,
    ReactiveFormsModule,
            TooltipModule,
            FormsModule,
            ToastModule,
            DialogModule,
            ConfirmDialogModule], providers: [provideHttpClient(withInterceptorsFromDi())
  ]
})
export class TravelModule { }
