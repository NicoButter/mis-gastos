import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';
import { FormsModule } from '@angular/forms';

export function validMonth(value: string): boolean {
  return /^[0-9]{4}-(0[1-9]|1[0-2])$/.test(value) && value >= '0001-01' && value <= '9999-11';
}

@Component({
  selector: 'gst-period-selector',
  imports: [FormsModule],
  template: `
    <div class="flex items-end gap-2 flex-wrap" aria-label="Período financiero">
      <button type="button" class="period-button" aria-label="Mes anterior" [disabled]="month() === '0001-01'" (click)="move(-1)">←</button>
      <label class="min-w-0 flex-1 max-w-xs text-sm font-semibold">Mes<input class="form-input" type="month" min="0001-01" max="9999-11" required [ngModel]="month()" (ngModelChange)="select($event)"></label>
      <button type="button" class="period-button" aria-label="Mes siguiente" [disabled]="month() === '9999-11'" (click)="move(1)">→</button>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PeriodSelectorComponent {
  readonly month = input.required<string>();
  readonly monthChange = output<string>();
  select(value: string): void { if (validMonth(value)) this.monthChange.emit(value); }
  move(direction: number): void {
    const [year, month] = this.month().split('-').map(Number);
    const index = year * 12 + month - 1 + direction;
    this.select(`${String(Math.floor(index / 12)).padStart(4, '0')}-${String(index % 12 + 1).padStart(2, '0')}`);
  }
}
