import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ViewAllocationPercentComponent } from './view-allocation-percent.component';

describe('ViewAllocationPercentComponent', () => {
  let component: ViewAllocationPercentComponent;
  let fixture: ComponentFixture<ViewAllocationPercentComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ViewAllocationPercentComponent]
    });
    fixture = TestBed.createComponent(ViewAllocationPercentComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
