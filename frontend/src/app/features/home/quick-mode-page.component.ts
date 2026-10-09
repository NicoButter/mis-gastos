import { ChangeDetectionStrategy, Component } from '@angular/core';

import { OperationFormComponent } from '../finance/operation-form.component';

@Component({
  imports: [OperationFormComponent],
  template: `
    <header><p class="text-sm font-semibold text-brand-700">Modo rápido</p><h1 class="mt-1 text-3xl font-black">Registrar un gasto</h1><p class="mt-2 text-slate-500">Importe, categoría y cuenta. Listo.</p></header>
    <section class="finance-card mt-6 max-w-xl mb-20"><gst-operation-form [quick]="true" /></section>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class QuickModePageComponent {}
