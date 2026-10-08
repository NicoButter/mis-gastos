import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { catchError, throwError } from 'rxjs';

function cookie(name: string): string | null {
  const match = document.cookie.split('; ').find((part) => part.startsWith(`${name}=`));
  return match ? decodeURIComponent(match.split('=')[1]) : null;
}

export const csrfInterceptor: HttpInterceptorFn = (request, next) => {
  const token = cookie('csrftoken');
  const unsafe = !['GET', 'HEAD', 'OPTIONS'].includes(request.method);
  return next(request.clone({ withCredentials: true, setHeaders: unsafe && token ? { 'X-CSRFToken': token } : {} }));
};

export const apiErrorInterceptor: HttpInterceptorFn = (request, next) => next(request).pipe(
  catchError((error: HttpErrorResponse) => {
    // UI state components consume normalized API errors in Phase 1; never log payloads.
    return throwError(() => error);
  }),
);
