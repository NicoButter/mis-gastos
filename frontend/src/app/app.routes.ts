import { Routes } from '@angular/router';

import { authGuard } from './core/auth.guard';
import { DashboardPageComponent } from './features/home/dashboard-page.component';
import { QuickModePageComponent } from './features/home/quick-mode-page.component';
import { LoginPageComponent } from './layouts/login-page.component';
import { PrivateLayoutComponent } from './layouts/private-layout.component';
import { PublicLayoutComponent } from './layouts/public-layout.component';

export const appRoutes: Routes = [
  { path: '', component: PublicLayoutComponent, title: 'Gastio' },
  { path: 'auth/login', component: LoginPageComponent, title: 'Ingresar | Gastio' },
  {
    path: 'app', component: PrivateLayoutComponent, canActivateChild: [authGuard], children: [
      { path: 'dashboard', component: DashboardPageComponent, title: 'Panel | Gastio' },
      { path: 'quick', component: QuickModePageComponent, title: 'Modo rápido | Gastio' },
      { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
    ],
  },
  { path: '**', redirectTo: '' },
];
