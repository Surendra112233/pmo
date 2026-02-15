import { ComponentFixture, TestBed } from '@angular/core/testing';

import { HardwareGridComponent } from './hardware-grid.component';

describe('HardwareGridComponent', () => {
  let component: HardwareGridComponent;
  let fixture: ComponentFixture<HardwareGridComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [HardwareGridComponent]
    });
    fixture = TestBed.createComponent(HardwareGridComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
