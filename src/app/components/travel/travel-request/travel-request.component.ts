import { CommonModule } from '@angular/common';
import { Component, ViewChild } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { MessageService } from 'primeng/api';
import { ButtonModule } from 'primeng/button';
import { DropdownModule } from 'primeng/dropdown';
import { InputTextModule } from 'primeng/inputtext';
import { Table, TableModule } from 'primeng/table';
import { TabViewModule } from 'primeng/tabview';
import { ToastModule } from 'primeng/toast';
import { ActivatedRouterService } from 'src/app/services/activated-router-service';
import { UserService } from 'src/app/services/user.service';
import { RequestsListComponent } from '../requests-list/requests-list.component';
import { CashAdvanceRequestsListComponent } from '../cash-advance-requests-list/cash-advance-requests-list.component';

@Component({
  selector: 'app-travel-request',
  templateUrl: './travel-request.component.html',
  styleUrls: ['./travel-request.component.scss'],
  imports: [ ToastModule, DropdownModule, ReactiveFormsModule, RequestsListComponent, CashAdvanceRequestsListComponent,
        TableModule, CommonModule, FormsModule, TabViewModule, TableModule, InputTextModule, ToastModule, ButtonModule],
  standalone: true
})

export class TravelRequestComponent {
  @ViewChild('dt2') dt : Table | undefined
  travelRequests:any =[];
  selectedSection: string = 'requests';

  constructor(
      private userService:UserService,
      private router:Router,    
      private messageService: MessageService,
      private activatedRouterService: ActivatedRouterService
  ) {}

  ngOnInit(){
    this.getRequests()
  }

  applyFilterGlobal($event:any, stringVal:any) {
    this.dt!.filterGlobal(($event.target as HTMLInputElement).value, stringVal);
  }

  selectSection(section: string) {
    this.selectedSection = section;
  }

  getRequests(){

  }

  navigateToRaiseRequest(){
    this.router.navigate(['/travel/raise-travel-request']);
  }

  navigateToView(requestId:any){

  }
}
