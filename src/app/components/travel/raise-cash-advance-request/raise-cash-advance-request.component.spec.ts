import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RaiseCashAdvanceRequestComponent } from './raise-cash-advance-request.component';

describe('RaiseCashAdvanceRequestComponent', () => {
  let component: RaiseCashAdvanceRequestComponent;
  let fixture: ComponentFixture<RaiseCashAdvanceRequestComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [RaiseCashAdvanceRequestComponent]
    });
    fixture = TestBed.createComponent(RaiseCashAdvanceRequestComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
