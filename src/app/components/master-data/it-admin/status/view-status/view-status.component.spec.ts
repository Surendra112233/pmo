import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ViewStatusComponent } from './view-status.component';

describe('ViewStatusComponent', () => {
  let component: ViewStatusComponent;
  let fixture: ComponentFixture<ViewStatusComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ViewStatusComponent]
    });
    fixture = TestBed.createComponent(ViewStatusComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
