import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ViewSoftwareComponent } from './view-software.component';

describe('ViewSoftwareComponent', () => {
  let component: ViewSoftwareComponent;
  let fixture: ComponentFixture<ViewSoftwareComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ViewSoftwareComponent]
    });
    fixture = TestBed.createComponent(ViewSoftwareComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
