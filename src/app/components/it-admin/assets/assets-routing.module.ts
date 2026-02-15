import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AuthGuard } from 'src/app/services/auth.guard';

const routes: Routes = [
  {
    path:'hardware',
    loadComponent: () => import('../assets/hardware/hardware-grid/hardware-grid.component').then(c => c.HardwareGridComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'add_hardware',
    loadComponent: () => import('../assets/hardware/add-hardware/add-hardware.component').then(c => c.AddHardwareComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'edit_hardware/:id',
    loadComponent: () => import('../assets/hardware/add-hardware/add-hardware.component').then(c => c.AddHardwareComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'view_hardware',
    loadComponent: () => import('../assets/hardware/view-hardware/view-hardware.component').then(c => c.ViewHardwareComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'software',
    loadComponent: () => import('../assets/software/software-grid/software-grid.component').then(c => c.SoftwareGridComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'add_software',
    loadComponent: () => import('../assets/software/add-software/add-software.component').then(c => c.AddSoftwareComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'edit_software/:id',
    loadComponent: () => import('../assets/software/add-software/add-software.component').then(c => c.AddSoftwareComponent),
    canActivate: [AuthGuard]
  },
  {
    path:'view_software',
    loadComponent: () => import('../assets/software/view-software/view-software.component').then(c => c.ViewSoftwareComponent),
    canActivate: [AuthGuard]
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class AssetsRoutingModule { }
