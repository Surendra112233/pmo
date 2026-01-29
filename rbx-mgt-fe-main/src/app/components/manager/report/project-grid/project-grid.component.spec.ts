import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ProjectGridComponent } from './project-grid.component';

describe('ProjectGridComponent', () => {
  let component: ProjectGridComponent;
  let fixture: ComponentFixture<ProjectGridComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ProjectGridComponent]
    });
    fixture = TestBed.createComponent(ProjectGridComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
