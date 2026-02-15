import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ViewHardwareComponent } from './view-hardware.component';

describe('ViewHardwareComponent', () => {
  let component: ViewHardwareComponent;
  let fixture: ComponentFixture<ViewHardwareComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ViewHardwareComponent]
    });
    fixture = TestBed.createComponent(ViewHardwareComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
