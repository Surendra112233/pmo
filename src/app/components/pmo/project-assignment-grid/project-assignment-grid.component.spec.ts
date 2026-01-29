import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ProjectAssignmentGridComponent } from './project-assignment-grid.component';

describe('ProjectAssignmentGridComponent', () => {
  let component: ProjectAssignmentGridComponent;
  let fixture: ComponentFixture<ProjectAssignmentGridComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProjectAssignmentGridComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(ProjectAssignmentGridComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
