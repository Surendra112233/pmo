import { Component, HostListener, inject, OnInit, ViewChild } from '@angular/core';
import { Router, RouterLink, RouterOutlet } from '@angular/router';
import { MatDrawer } from '@angular/material/sidenav';
import { MatButtonModule } from '@angular/material/button';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatMenuModule } from '@angular/material/menu';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { RouterModule, Routes } from '@angular/router';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatTooltipModule } from '@angular/material/tooltip';
import { CommonModule } from '@angular/common';
import { MaterialModule } from '../../material-module';
import { LoginService} from '../../services/login.service';
import { ToastModule } from 'primeng/toast';

@Component({
  selector: 'app-menubar',
  imports: [
    RouterLink,
    RouterOutlet,
    CommonModule,
    RouterOutlet,
    ToastModule
  ], standalone: true,
  templateUrl: './menubar.component.html',
  styleUrls: ['./menubar.component.scss']
})
export class MenubarComponent implements OnInit{

  userName:string='';
  roles:any;
  designation:string='';

  constructor(
    private router: Router,
    private loginService:LoginService
  ){}

  isSidebarCollapsed = false;
  isProfileMenuOpen = false;

  ngOnInit() {
    this.userName=localStorage.getItem('user_name')||'';
    this.designation=localStorage.getItem('designation')||'';
    this.roles=localStorage.getItem('Roles') || '';
    // this.roles = this.roles.split(',');
    // this.roles = 'UserAdmin'
  }


  toggleSidebar() {
    this.isSidebarCollapsed = !this.isSidebarCollapsed;
  }

  toggleProfileMenu() {
    this.isProfileMenuOpen = !this.isProfileMenuOpen;
  }

  // Detect click anywhere on the screen
  @HostListener('document:click', ['$event'])
  onClickOutside(event: Event) {
    const targetElement = event.target as HTMLElement;

    // Check if the clicked element is inside the profile menu or the profile icon
    if (!targetElement.closest('.profile')) {
      this.isProfileMenuOpen = false;
    }
  }

  logout() {
    localStorage.clear();
    this.loginService.logout();
  }

  isActive(routes: string | string[]): boolean {
    return Array.isArray(routes) ? routes.some(route => this.router.url.includes(route)) : this.router.url.includes(routes);
  }
}
