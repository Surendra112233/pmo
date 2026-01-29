import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PmoReportSummaryComponent } from './pmo-report-summary.component';

describe('PmoReportSummaryComponent', () => {
  let component: PmoReportSummaryComponent;
  let fixture: ComponentFixture<PmoReportSummaryComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [PmoReportSummaryComponent]
    });
    fixture = TestBed.createComponent(PmoReportSummaryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
