import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ManagerMeterGaugeComponent } from './manager-meter-gauge.component';

describe('ManagerMeterGaugeComponent', () => {
  let component: ManagerMeterGaugeComponent;
  let fixture: ComponentFixture<ManagerMeterGaugeComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ManagerMeterGaugeComponent]
    });
    fixture = TestBed.createComponent(ManagerMeterGaugeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
