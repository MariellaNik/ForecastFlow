import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { DashboardComponent } from './dashboard/dashboard.component';
import { HomeComponent } from './home/home.component';

const routes: Routes = [
  {
    path: '',
    component: HomeComponent,      
    //canActivate: [AuthGuardService]  
  },
  {
    path: 'dashboard',
    component: DashboardComponent,      
    //canActivate: [AuthGuardService]  
  },
];

@NgModule({

  
  exports: [RouterModule],
  declarations: [DashboardComponent],
  imports: [RouterModule.forRoot(routes)]
})
export class AppRoutingModule { }
