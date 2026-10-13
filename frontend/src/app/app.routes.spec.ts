import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter, Router } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';

import { safeInternalReturnUrl } from './core/auth.guard';
import { NotFoundPageComponent } from './features/marketing/not-found-page.component';
import { appRoutes } from './app.routes';

describe('application routes', () => {
  beforeEach(() => TestBed.configureTestingModule({ providers: [provideHttpClient(), provideRouter(appRoutes)] }));

  it('serves the landing publicly', async () => {
    const harness = await RouterTestingHarness.create();
    await harness.navigateByUrl('/');
    expect(TestBed.inject(Router).url).toBe('/');
    expect(harness.routeNativeElement?.textContent).toContain('Tomá el control de tu dinero');
  });

  it('navigates publicly to login', async () => {
    const harness = await RouterTestingHarness.create();
    await harness.navigateByUrl('/login');
    expect(TestBed.inject(Router).url).toBe('/login');
    expect(harness.routeNativeElement?.textContent).toContain('Ingresá a Gastio');
    expect(harness.routeNativeElement?.textContent).toContain('Privacidad');
  });

  it('serves all information pages publicly and identifies pending legal documents', async () => {
    const pages = [
      ['/terminos', 'Términos y condiciones de uso', 'No vigente; pendiente de aprobación'],
      ['/privacidad', 'Política de privacidad', 'No vigente; pendiente de aprobación'],
      ['/como-funciona', 'Cómo funciona Gastio', 'No aplica; guía informativa'],
      ['/seguridad', 'Seguridad y protección de datos', 'No aplica; resumen informativo'],
    ];
    const harness = await RouterTestingHarness.create();

    for (const [path, title, status] of pages) {
      await harness.navigateByUrl(path);
      expect(TestBed.inject(Router).url).toBe(path);
      expect(harness.routeNativeElement?.textContent).toContain(title);
      expect(harness.routeNativeElement?.textContent).toContain(status);
    }
  });

  it('redirects an anonymous visitor from the private shell without a loop', async () => {
    const harness = await RouterTestingHarness.create();
    await harness.navigateByUrl('/app/transactions');
    expect(TestBed.inject(Router).url).toBe('/login?returnUrl=%2Fapp%2Ftransactions');
    expect(harness.routeNativeElement?.textContent).toContain('Ingresá a Gastio');
  });

  it('renders a professional not-found route instead of redirecting to the landing', async () => {
    const harness = await RouterTestingHarness.create();
    await harness.navigateByUrl('/not-a-route', NotFoundPageComponent);
    expect(TestBed.inject(Router).url).toBe('/not-a-route');
  });

  it('preserves only internal private destinations', () => {
    expect(safeInternalReturnUrl('/app/quick')).toBe('/app/quick');
    expect(safeInternalReturnUrl('//external.example')).toBeNull();
    expect(safeInternalReturnUrl('https://external.example')).toBeNull();
  });
});
