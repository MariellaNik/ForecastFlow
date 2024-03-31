import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
    isAuthenticated = false;
  
    constructor() {}
  
    login(username: string, password: string): boolean {
      //authentication logic
      this.isAuthenticated = true;
      return true;
    }
  
    logout(): void {
      // Perform logout logic, such as clearing tokens or session data.
      this.isAuthenticated = false;
    }
  
    isAuthenticatedFunc(): boolean {
      return this.isAuthenticated;
    }
  }
export class AuthGuard implements CanActivate {

  constructor(private authService: AuthService, private router: Router) { }

  canActivate(): boolean {
    if (this.authService.isAuthenticatedFunc()) {
      return true; 
    } else {
      this.router.navigateByUrl('/login');
      return false;
    }
  }
}
