import { Injectable, computed, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly authenticated = signal(false);
  readonly isAuthenticated = computed(() => this.authenticated());

  // Phase 1 will hydrate this state from /api/v1/auth/me/ using secure cookies.
  setAuthenticated(value: boolean): void { this.authenticated.set(value); }
}
