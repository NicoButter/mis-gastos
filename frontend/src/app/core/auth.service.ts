import { DOCUMENT } from '@angular/common';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

export interface AuthenticatedUser {
  id: string;
  email: string;
  displayName: string;
}

export interface ActiveHousehold {
  id: string;
  name: string;
  role: string;
}

export type AuthStatus = 'anonymous' | 'authenticated';

interface SessionResponse {
  user: AuthenticatedUser;
  households: ActiveHousehold[];
  activeHousehold: ActiveHousehold | null;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  readonly sessionEndpoint = '/api/v1/auth/me/';
  readonly logoutEndpoint = '/api/v1/auth/logout/';
  readonly googleLoginEndpoint = '/accounts/google/login/';
  private readonly csrfEndpoint = '/api/v1/auth/csrf/';
  private readonly configurationEndpoint = '/api/v1/auth/config/';
  private readonly householdsEndpoint = '/api/v1/households/';
  private readonly http = inject(HttpClient);
  private readonly document = inject(DOCUMENT);
  readonly status = signal<AuthStatus>('anonymous');
  readonly currentUser = signal<AuthenticatedUser | null>(null);
  readonly activeHousehold = signal<ActiveHousehold | null>(null);
  readonly households = signal<ActiveHousehold[]>([]);
  readonly googleLoginEnabled = signal(false);
  readonly isLoading = signal(false);
  readonly error = signal<string | null>(null);
  readonly isAuthenticated = computed(() => this.status() === 'authenticated');

  async initialize(): Promise<void> {
    this.isLoading.set(true);
    this.error.set(null);
    try {
      const configuration = await firstValueFrom(this.http.get<{ googleLoginEnabled: boolean }>(this.configurationEndpoint));
      this.googleLoginEnabled.set(configuration.googleLoginEnabled);
      const session = await firstValueFrom(this.http.get<SessionResponse>(this.sessionEndpoint));
      this.applySession(session);
    } catch (error: unknown) {
      this.markAnonymous();
      if (!(error instanceof HttpErrorResponse) || ![401, 403].includes(error.status)) {
        this.error.set('No se pudo comprobar la sesión. Intentá nuevamente.');
      }
    } finally {
      this.isLoading.set(false);
    }
  }

  markAnonymous(): void {
    this.status.set('anonymous');
    this.currentUser.set(null);
    this.activeHousehold.set(null);
    this.households.set([]);
    this.isLoading.set(false);
  }

  async startGoogleLogin(): Promise<void> {
    if (!this.googleLoginEnabled()) {
      this.error.set('El acceso con Google todavía no está configurado en este entorno.');
      return;
    }
    this.isLoading.set(true);
    this.error.set(null);
    try {
      const csrf = await firstValueFrom(this.http.get<{ csrfToken: string }>(this.csrfEndpoint));
      const form = this.document.createElement('form');
      form.method = 'post';
      form.action = this.googleLoginEndpoint;
      form.style.display = 'none';
      const token = this.document.createElement('input');
      token.type = 'hidden';
      token.name = 'csrfmiddlewaretoken';
      token.value = csrf.csrfToken;
      form.appendChild(token);
      this.document.body.appendChild(form);
      form.submit();
    } catch {
      this.isLoading.set(false);
      this.error.set('No se pudo iniciar el acceso con Google. Intentá nuevamente.');
    }
  }

  async logout(): Promise<void> {
    this.isLoading.set(true);
    try {
      await firstValueFrom(this.http.get(this.csrfEndpoint));
      await firstValueFrom(this.http.post(this.logoutEndpoint, {}));
      this.markAnonymous();
    } catch {
      this.error.set('No se pudo cerrar la sesión. Intentá nuevamente.');
    } finally {
      this.isLoading.set(false);
    }
  }

  async createFirstHousehold(name: string): Promise<boolean> {
    this.isLoading.set(true);
    this.error.set(null);
    try {
      const response = await firstValueFrom(this.http.post<{ activeHousehold: ActiveHousehold }>(this.householdsEndpoint, { name }));
      this.activeHousehold.set(response.activeHousehold);
      this.households.update((items) => [...items, response.activeHousehold]);
      return true;
    } catch {
      this.error.set('No se pudo crear el hogar. Revisá el nombre e intentá nuevamente.');
      return false;
    } finally {
      this.isLoading.set(false);
    }
  }

  async selectHousehold(householdId: string): Promise<void> {
    const response = await firstValueFrom(this.http.post<{ activeHousehold: ActiveHousehold }>('/api/v1/auth/active-household/', { householdId }));
    this.activeHousehold.set(response.activeHousehold);
  }

  private applySession(session: SessionResponse): void {
    this.status.set('authenticated');
    this.currentUser.set(session.user);
    this.households.set(session.households);
    this.activeHousehold.set(session.activeHousehold);
    this.error.set(null);
  }
}
