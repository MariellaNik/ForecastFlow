import { Component } from '@angular/core';
import { Route, Router } from '@angular/router';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  title = 'ForecastFlow';
  
  constructor(private router: Router) {}

  navigateToDashboard() {
    this.router.navigate(['/login']);
  }
}
