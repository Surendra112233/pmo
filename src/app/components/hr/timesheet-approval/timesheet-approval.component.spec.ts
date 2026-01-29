import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TimesheetApprovalComponent } from './timesheet-approval.component';

describe('TimesheetApprovalComponent', () => {
  let component: TimesheetApprovalComponent;
  let fixture: ComponentFixture<TimesheetApprovalComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [TimesheetApprovalComponent]
    });
    fixture = TestBed.createComponent(TimesheetApprovalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
