import { ChangeDetectionStrategy, Component, input } from '@angular/core';

@Component({
  selector: 'gst-ui-state',
  template: `
    <section class="rounded-2xl border border-slate-200 bg-white p-6 text-center shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <p class="text-sm font-semibold text-brand-700 dark:text-teal-300">{{ label() }}</p>
      <h2 class="mt-2 text-lg font-bold">{{ title() }}</h2>
      <p class="mt-2 text-sm text-slate-600 dark:text-slate-300">{{ detail() }}</p>
    </section>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class UiStateComponent {
  readonly label = input.required<string>();
  readonly title = input.required<string>();
  readonly detail = input.required<string>();
}
