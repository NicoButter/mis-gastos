import { Routes } from '@angular/router';

import { authChildGuard, authGuard, onboardingGuard } from './core/auth.guard';
import { AuthLayoutComponent } from './layouts/auth-layout.component';
import { LoginPageComponent } from './layouts/login-page.component';
import { PrivateLayoutComponent } from './layouts/private-layout.component';
import { PublicLayoutComponent } from './layouts/public-layout.component';

export const appRoutes: Routes = [
  {
    path: '', component: PublicLayoutComponent, children: [
      {
        path: '',
        title: 'Gastio | Finanzas familiares claras',
        loadComponent: () => import('./features/marketing/landing-page.component').then((m) => m.LandingPageComponent),
      },
      { path: 'terminos', title: 'Términos y condiciones | Gastio', data: { document: 'terms' }, loadComponent: () => import('./features/marketing/public-information-page.component').then((m) => m.PublicInformationPageComponent) },
      { path: 'privacidad', title: 'Política de privacidad | Gastio', data: { document: 'privacy' }, loadComponent: () => import('./features/marketing/public-information-page.component').then((m) => m.PublicInformationPageComponent) },
      { path: 'como-funciona', title: 'Cómo funciona | Gastio', data: { document: 'howItWorks' }, loadComponent: () => import('./features/marketing/public-information-page.component').then((m) => m.PublicInformationPageComponent) },
      { path: 'seguridad', title: 'Seguridad y datos | Gastio', data: { document: 'security' }, loadComponent: () => import('./features/marketing/public-information-page.component').then((m) => m.PublicInformationPageComponent) },
    ],
  },
  {
    path: 'onboarding', canActivate: [onboardingGuard], title: 'Crear hogar | Gastio',
    loadComponent: () => import('./features/home/onboarding-page.component').then((m) => m.OnboardingPageComponent),
  },
  {
    path: 'login', component: AuthLayoutComponent, children: [
      { path: '', component: LoginPageComponent, title: 'Ingresar | Gastio' },
    ],
  },
  {
    path: 'app', component: PrivateLayoutComponent, canActivate: [authGuard], canActivateChild: [authChildGuard], children: [
      { path: 'quick', title: 'Modo rápido | Gastio', loadComponent: () => import('./features/home/quick-mode-page.component').then((m) => m.QuickModePageComponent) },
      { path: 'transactions', title: 'Movimientos | Gastio', loadComponent: () => import('./features/finance/transactions-page.component').then((m) => m.TransactionsPageComponent) },
      { path: 'accounts', title: 'Cuentas | Gastio', loadComponent: () => import('./features/finance/accounts-page.component').then((m) => m.AccountsPageComponent) },
      { path: 'installments', title: 'Compras en cuotas | Gastio', data: { installmentsOnly: true }, loadComponent: () => import('./features/finance/cards-page.component').then(m => m.CardsPageComponent) },
      { path: 'recurring', title: 'Gastos recurrentes | Gastio', loadComponent: () => import('./features/finance/recurring-page.component').then(m => m.RecurringPageComponent) },
      { path: 'cards', title: 'Tarjetas | Gastio', loadComponent: () => import('./features/finance/cards-page.component').then(m => m.CardsPageComponent) },
      { path: 'categories', title: 'Categorías | Gastio', loadComponent: () => import('./features/finance/categories-page.component').then((m) => m.CategoriesPageComponent) },
      { path: 'households', title: 'Hogares | Gastio', data: { title: 'Hogares', detail: 'La gestión de hogares se habilitará junto a autenticación e invitaciones.' }, loadComponent: () => import('./features/home/app-placeholder-page.component').then((m) => m.AppPlaceholderPageComponent) },
      { path: 'settings', title: 'Configuración | Gastio', data: { title: 'Configuración', detail: 'Las preferencias estarán disponibles al conectar la sesión.' }, loadComponent: () => import('./features/home/app-placeholder-page.component').then((m) => m.AppPlaceholderPageComponent) },
      { path: 'dashboard', pathMatch: 'full', redirectTo: '' },
      { path: '', pathMatch: 'full', title: 'Panel | Gastio', loadComponent: () => import('./features/home/dashboard-page.component').then((m) => m.DashboardPageComponent) },
    ],
  },
  { path: '**', title: 'Página no encontrada | Gastio', loadComponent: () => import('./features/marketing/not-found-page.component').then((m) => m.NotFoundPageComponent) },
];
