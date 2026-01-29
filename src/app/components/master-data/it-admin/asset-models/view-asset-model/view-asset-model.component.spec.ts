import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ViewAssetModelComponent } from './view-asset-model.component';

describe('ViewAssetModelComponent', () => {
  let component: ViewAssetModelComponent;
  let fixture: ComponentFixture<ViewAssetModelComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ViewAssetModelComponent]
    });
    fixture = TestBed.createComponent(ViewAssetModelComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
