import { bootstrapApplication } from '@angular/platform-browser';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideRouter } from '@angular/router';

import { AppComponent } from './app/app.component';
import { appRoutes } from './app/app.routes';
import { apiErrorInterceptor, csrfInterceptor } from './app/core/http.interceptors';

bootstrapApplication(AppComponent, {
  providers: [provideRouter(appRoutes), provideHttpClient(withInterceptors([csrfInterceptor, apiErrorInterceptor]))],
}).catch((error: unknown) => console.error('No se pudo iniciar Gastio', error));
