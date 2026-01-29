import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ViewProjectRolesComponent } from './view-project-roles.component';

describe('ViewProjectRolesComponent', () => {
  let component: ViewProjectRolesComponent;
  let fixture: ComponentFixture<ViewProjectRolesComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ViewProjectRolesComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(ViewProjectRolesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
