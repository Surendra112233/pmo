import { Directive, Input, OnInit } from '@angular/core';
import { AbstractControl, ValidationErrors, Validator, ValidatorFn, NG_VALIDATORS } from '@angular/forms';

@Directive({
  selector: '[appDateComparison]',
  standalone: true,
  providers: [
    {
      provide: NG_VALIDATORS,
      useExisting: DateComparisonDirective,
      multi: true,
    },
  ],
})
export class DateComparisonDirective implements Validator, OnInit {

  @Input() issuedDateField!: string; // Name of the issued date control
  @Input() validTillDateField!: string; // Name of the valid till date control

  private validator: ValidatorFn = () => null; // Default validator

  ngOnInit() {
    this.validator = this.dateComparisonValidator(this.issuedDateField, this.validTillDateField);
  }

  validate(control: AbstractControl): ValidationErrors | null {
    return this.validator(control);
  }

  private dateComparisonValidator(issuedDateField: string, validTillDateField: string): ValidatorFn {
    return (formGroup: AbstractControl): ValidationErrors | null => {
      const issuedDate = formGroup.get(issuedDateField)?.value;
      const validTillDate = formGroup.get(validTillDateField)?.value;

      if (issuedDate && validTillDate && new Date(validTillDate) <= new Date(issuedDate)) {
        return { validTillInvalid: true };
      }
      return null;
    };
  }
}
