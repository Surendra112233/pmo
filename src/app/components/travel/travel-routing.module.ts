import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AuthGuard } from 'src/app/services/auth.guard';

const routes: Routes = [
  {
    path:'travel-requests',
    loadComponent: () => import('./travel-request/travel-request.component').then(c => c.TravelRequestComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'raise-travel-request',
    loadComponent: () => import('./raise-travel-request/raise-travel-request.component').then(c => c.RaiseTravelRequestComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'view-travel-request',
    loadComponent: () => import('./view-travel-request/view-travel-request.component').then(c => c.ViewTravelRequestComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'edit_travel_request',
    loadComponent: () => import('./edit-travel-request/edit-travel-request.component').then(c => c.EditTravelRequestComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'raise-cash-advance-request',
    loadComponent: () => import('./raise-cash-advance-request/raise-cash-advance-request.component').then(c => c.RaiseCashAdvanceRequestComponent),
    canActivate: [AuthGuard]
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class TravelRoutingModule { }
