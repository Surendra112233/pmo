import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RaiseTravelRequestComponent } from './raise-travel-request.component';

describe('RaiseTravelRequestComponent', () => {
  let component: RaiseTravelRequestComponent;
  let fixture: ComponentFixture<RaiseTravelRequestComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [RaiseTravelRequestComponent]
    });
    fixture = TestBed.createComponent(RaiseTravelRequestComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
