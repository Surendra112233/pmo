import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { LoginService } from '../services/login.service';

@Component({
    selector: 'app-loader',
    imports: [CommonModule],
    templateUrl: './loader.component.html',
    styleUrls: ['./loader.component.scss'],
    standalone:true
})
export class LoaderComponent {
  isLoading:boolean=false
  constructor(private apiService: LoginService) {}
  ngOnInit(): void {
    // Subscribe to the loader's state observable
    this.apiService.loading$.subscribe((loading: boolean) => {
      this.isLoading = loading; // Update the state
    });
  }
}
