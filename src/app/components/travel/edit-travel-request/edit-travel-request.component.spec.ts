import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EditTravelRequestComponent } from './edit-travel-request.component';

describe('EditTravelRequestComponent', () => {
  let component: EditTravelRequestComponent;
  let fixture: ComponentFixture<EditTravelRequestComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [EditTravelRequestComponent]
    });
    fixture = TestBed.createComponent(EditTravelRequestComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
