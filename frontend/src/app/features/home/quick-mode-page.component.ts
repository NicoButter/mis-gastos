import { ChangeDetectionStrategy, Component } from '@angular/core';

import { UiStateComponent } from '../../shared/ui-state.component';

@Component({
  imports: [UiStateComponent],
  template: `
    <header><p class="text-sm font-semibold text-brand-700 dark:text-teal-300">Modo rápido</p><h1 class="mt-1 text-3xl font-black">Registrar un gasto</h1><p class="mt-2 text-slate-600 dark:text-slate-300">Flujo móvil preparado para monto, categoría y cuenta.</p></header>
    <div class="mt-8 max-w-xl"><gst-ui-state label="Estructura lista" title="Aún no registra movimientos" detail="La persistencia se habilitará solo al implementar la fase financiera correspondiente." /></div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class QuickModePageComponent {}
