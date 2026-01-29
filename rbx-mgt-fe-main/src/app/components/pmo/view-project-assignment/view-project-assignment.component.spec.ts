import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ViewProjectAssignmentComponent } from './view-project-assignment.component';

describe('ViewProjectAssignmentComponent', () => {
  let component: ViewProjectAssignmentComponent;
  let fixture: ComponentFixture<ViewProjectAssignmentComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ViewProjectAssignmentComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(ViewProjectAssignmentComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
