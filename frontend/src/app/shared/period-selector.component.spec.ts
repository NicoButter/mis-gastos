import { TestBed } from '@angular/core/testing';
import { vi } from 'vitest';
import { PeriodSelectorComponent, validMonth } from './period-selector.component';

describe('financial period navigation', () => {
  it('moves across year boundaries and accepts month/year selection', () => {
    const fixture = TestBed.createComponent(PeriodSelectorComponent);
    fixture.componentRef.setInput('month', '2026-01');
    const emit = vi.spyOn(fixture.componentInstance.monthChange, 'emit');
    fixture.componentInstance.move(-1); expect(emit).toHaveBeenLastCalledWith('2025-12');
    fixture.componentRef.setInput('month', '2026-12');
    fixture.componentInstance.move(1); expect(emit).toHaveBeenLastCalledWith('2027-01');
    fixture.componentInstance.select('2024-02'); expect(emit).toHaveBeenLastCalledWith('2024-02');
    emit.mockClear(); fixture.componentInstance.select(''); fixture.componentInstance.select('2026-13');
    expect(emit).not.toHaveBeenCalled();
  });
  it('rejects periods outside the API range', () => {
    expect(validMonth('0000-12')).toBe(false); expect(validMonth('9999-12')).toBe(false);
    expect(validMonth('0001-01')).toBe(true); expect(validMonth('9999-11')).toBe(true);
  });
});
