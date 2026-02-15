import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AssetCategoriesComponent } from './asset-categories.component';

describe('AssetCategoriesComponent', () => {
  let component: AssetCategoriesComponent;
  let fixture: ComponentFixture<AssetCategoriesComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [AssetCategoriesComponent]
    });
    fixture = TestBed.createComponent(AssetCategoriesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
