import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CashAdvanceRequestsListComponent } from './cash-advance-requests-list.component';

describe('CashAdvanceRequestsListComponent', () => {
  let component: CashAdvanceRequestsListComponent;
  let fixture: ComponentFixture<CashAdvanceRequestsListComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [CashAdvanceRequestsListComponent]
    });
    fixture = TestBed.createComponent(CashAdvanceRequestsListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
