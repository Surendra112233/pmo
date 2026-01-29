import { ComponentFixture, TestBed } from '@angular/core/testing';

import { HrEmpReportComponent } from './hr-emp-report.component';

describe('HrEmpReportComponent', () => {
  let component: HrEmpReportComponent;
  let fixture: ComponentFixture<HrEmpReportComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [HrEmpReportComponent]
    });
    fixture = TestBed.createComponent(HrEmpReportComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
