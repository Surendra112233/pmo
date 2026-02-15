import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MaintainUserGridComponent } from './maintain-user-grid.component';

describe('MaintainUserGridComponent', () => {
  let component: MaintainUserGridComponent;
  let fixture: ComponentFixture<MaintainUserGridComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MaintainUserGridComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(MaintainUserGridComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
