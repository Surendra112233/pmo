import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AddHardwareComponent } from './add-hardware.component';

describe('AddHardwareComponent', () => {
  let component: AddHardwareComponent;
  let fixture: ComponentFixture<AddHardwareComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [AddHardwareComponent]
    });
    fixture = TestBed.createComponent(AddHardwareComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
