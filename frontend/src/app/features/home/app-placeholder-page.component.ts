import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

import { UiStateComponent } from '../../shared/ui-state.component';

@Component({
  imports: [UiStateComponent],
  template: `<header><p class="text-sm font-semibold text-brand-700 dark:text-teal-300">Espacio privado</p><h1 class="mt-1 text-3xl font-black">{{ title }}</h1></header><div class="mt-8 max-w-xl"><gst-ui-state label="Próximamente" [title]="title" [detail]="detail" /></div>`,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AppPlaceholderPageComponent {
  private readonly route = inject(ActivatedRoute);
  readonly title = this.route.snapshot.data['title'] as string;
  readonly detail = this.route.snapshot.data['detail'] as string;
}
