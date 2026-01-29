import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TimesheetViewComponent } from './timesheet-view.component';

describe('TimesheetViewComponent', () => {
  let component: TimesheetViewComponent;
  let fixture: ComponentFixture<TimesheetViewComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TimesheetViewComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(TimesheetViewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
