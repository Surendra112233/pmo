import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { LoginComponent } from './components/login/login.component';
import { ForgotPasswordComponent } from './components/forgot-password/forgot-password.component';
import { MenubarComponent } from './components/menubar/menubar.component';

export const routes: Routes = [
    {
        path: '',
        redirectTo:'login',
        pathMatch: 'full'
    },
    {
        path:'login',
        component: LoginComponent
    }, 
    {
        path:'forgot_password',
        component: ForgotPasswordComponent
    }, 
    {
        path:'',
       component:MenubarComponent,
        children:[
            {
                path:'um',
                loadChildren:() => import('../app/components/user-management/user-management.module').then(m => m.UserManagementModule),
                data: { breadcrumb: 'User Management' }
            }
        ]
        //     {
        //         path:'md',
        //         loadChildren:() => import('./pages/master-data/master-data.module').then(m => m.MasterDataModule),
        //         data: { breadcrumb: 'Master Data' }
        //     },
        //     {
        //         path:'pmo',
        //         loadChildren:() => import('./pages/pmo/pmo.module').then(m => m.PMOModule),
        //         data: { breadcrumb: 'PMO' }
        //     },
        //     {
        //         path:'emp',
        //         loadChildren:() => import('./pages/employee-timesheet/employee.module').then(m => m.EmployeeModule),
        //         data: { breadcrumb: 'Employee' }
        //     },
        //     {
        //         path:'mng',
        //         loadChildren:() => import('./pages/manager/manager.module').then(m => m.ManagerModule),
        //         data: { breadcrumb: 'Manager' }
        //     }
        // ]
    }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
