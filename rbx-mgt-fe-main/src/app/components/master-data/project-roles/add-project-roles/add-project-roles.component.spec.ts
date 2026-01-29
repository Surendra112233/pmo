import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AddProjectRolesComponent } from './add-project-roles.component';

describe('AddProjectRolesComponent', () => {
  let component: AddProjectRolesComponent;
  let fixture: ComponentFixture<AddProjectRolesComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AddProjectRolesComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(AddProjectRolesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
