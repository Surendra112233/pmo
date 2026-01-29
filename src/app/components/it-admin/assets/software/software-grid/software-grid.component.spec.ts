import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SoftwareGridComponent } from './software-grid.component';

describe('SoftwareGridComponent', () => {
  let component: SoftwareGridComponent;
  let fixture: ComponentFixture<SoftwareGridComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [SoftwareGridComponent]
    });
    fixture = TestBed.createComponent(SoftwareGridComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
