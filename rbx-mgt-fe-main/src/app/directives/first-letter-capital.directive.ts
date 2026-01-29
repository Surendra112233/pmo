import { Directive, HostListener } from '@angular/core';
import { NgControl } from '@angular/forms';

@Directive({
  selector: '[appFirstLetterCapital]',
  standalone: true
})
export class FirstLetterCapitalDirective {

  constructor(private control: NgControl) {}

  @HostListener('input', ['$event'])
  onInput(event: any): void {
    const value: string = event.target.value;
    if (value && value.length > 0) {
      const capitalizedValue = value.charAt(0).toUpperCase() + value.slice(1);
      this.control.control?.setValue(capitalizedValue, { emitEvent: false });
    }
  }

}

@Directive({
  selector: '[appAllLetterCapital]',
  standalone: true
})

export class AllLetterCapitalDirective {

  constructor(private control: NgControl) {}

  @HostListener('input', ['$event'])
  onInput(event: any): void {
    const value: string = event.target.value;
    if (value && value.length > 0) {
      const capitalizedValue = value.toUpperCase();
      this.control.control?.setValue(capitalizedValue, { emitEvent: false });
    }
  }

}
