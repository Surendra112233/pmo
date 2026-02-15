import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AddAllocationPercentComponent } from './add-allocation-percent.component';

describe('AddAllocationPercentComponent', () => {
  let component: AddAllocationPercentComponent;
  let fixture: ComponentFixture<AddAllocationPercentComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [AddAllocationPercentComponent]
    });
    fixture = TestBed.createComponent(AddAllocationPercentComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
