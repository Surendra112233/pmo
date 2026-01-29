import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';

export function lengthValidator(minLength: number, maxLength: number): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const value = control.value;
    if (!value) {
      return null; // Don't validate empty value if required validation is handled separately
    }

    const isValidLength = value.length >= minLength && value.length <= maxLength;

    return isValidLength ? null : { invalidLength: { minLength, maxLength } };
  };
}
