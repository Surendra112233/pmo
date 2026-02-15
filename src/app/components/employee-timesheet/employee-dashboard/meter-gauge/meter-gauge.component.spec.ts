import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MeterGaugeComponent } from './meter-gauge.component';

describe('MeterGaugeComponent', () => {
  let component: MeterGaugeComponent;
  let fixture: ComponentFixture<MeterGaugeComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [MeterGaugeComponent]
    });
    fixture = TestBed.createComponent(MeterGaugeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
