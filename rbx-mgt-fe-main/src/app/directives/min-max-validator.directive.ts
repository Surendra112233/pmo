import { Directive, Input } from '@angular/core';
import { AbstractControl, NG_VALIDATORS, ValidationErrors, Validator } from '@angular/forms';


@Directive({
  selector: '[appMinMaxValidator]',
  standalone: true,
  providers: [
    {
      provide: NG_VALIDATORS,
      useExisting: MinMaxValidatorDirective,
      multi: true,
    },
  ],
})
export class MinMaxValidatorDirective implements Validator {

  constructor() { }

  @Input() minLength: number = 0;
  @Input() maxLength: number = Infinity;

  validate(control: AbstractControl): ValidationErrors | null {
    const value: string = control.value || '';

    if (value.length < this.minLength) {
      return { minLength: `Minimum length is ${this.minLength}` };
    }

    if (value.length > this.maxLength) {
      return { maxLength: `Maximum length is ${this.maxLength}` };
    }
    return null;
  }

}
