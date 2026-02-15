import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AddAssetModelComponent } from './add-asset-model.component';

describe('AddAssetModelComponent', () => {
  let component: AddAssetModelComponent;
  let fixture: ComponentFixture<AddAssetModelComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [AddAssetModelComponent]
    });
    fixture = TestBed.createComponent(AddAssetModelComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
