import { TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { ActivatedRouteSnapshot, provideRouter, Router, RouterStateSnapshot, UrlTree } from '@angular/router';

import { authChildGuard } from './auth.guard';
import { AuthService } from './auth.service';

describe('private child route access', () => {
  const authenticated = signal(true);
  const households = signal([{ id: 'home-a' }]);

  beforeEach(() => {
    authenticated.set(true);
    households.set([{ id: 'home-a' }]);
    TestBed.configureTestingModule({ providers: [
      provideRouter([]),
      { provide: AuthService, useValue: { isAuthenticated: authenticated, households } },
    ] });
  });

  function check() {
    return TestBed.runInInjectionContext(() => authChildGuard(
      {} as ActivatedRouteSnapshot, { url: '/app/accounts' } as RouterStateSnapshot,
    ));
  }

  it('allows authenticated members', () => {
    expect(check()).toBe(true);
  });

  it('checks household access again when navigating inside the private shell', () => {
    expect(check()).toBe(true);
    households.set([]);
    expect(TestBed.inject(Router).serializeUrl(check() as UrlTree)).toBe('/onboarding');
  });

  it('redirects to login after logout', () => {
    authenticated.set(false);
    expect(TestBed.inject(Router).serializeUrl(check() as UrlTree)).toBe('/login?returnUrl=%2Fapp%2Faccounts');
  });
});
