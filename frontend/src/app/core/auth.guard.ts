import { inject } from '@angular/core';
import { CanActivateChildFn, CanActivateFn, Router, RouterStateSnapshot } from '@angular/router';

import { AuthService } from './auth.service';

export function safeInternalReturnUrl(value: string): string | null {
  return value.startsWith('/app') && !value.startsWith('//') && !value.includes('://') ? value : null;
}

function redirectAnonymousUser(state: RouterStateSnapshot): boolean | ReturnType<Router['createUrlTree']> {
  const auth = inject(AuthService);
  if (auth.isAuthenticated()) {
    return true;
  }
  const returnUrl = safeInternalReturnUrl(state.url);
  return inject(Router).createUrlTree(['/login'], { queryParams: returnUrl ? { returnUrl } : {} });
}

export const onboardingGuard: CanActivateFn = (_route, state) => {
  const auth = inject(AuthService);
  if (!auth.isAuthenticated()) return redirectAnonymousUser(state);
  return auth.households().length === 0 ? true : inject(Router).createUrlTree(['/app']);
};

export const householdContextGuard: CanActivateFn = (_route, state) => {
  const auth = inject(AuthService);
  if (!auth.isAuthenticated()) return redirectAnonymousUser(state);
  return auth.households().length === 0
    ? inject(Router).createUrlTree(['/onboarding'])
    : true;
};

export const authGuard: CanActivateFn = (_route, state) => householdContextGuard(_route, state);
export const authChildGuard: CanActivateChildFn = (_route, state) => redirectAnonymousUser(state);
