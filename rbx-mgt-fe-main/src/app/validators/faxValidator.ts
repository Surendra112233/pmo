import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';

export function faxValidator(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const value = control.value;

    // If the field is empty, validation passes (use `required` validator for mandatory fields)
    if (!value) {
      return null;
    }

    // Regex to allow numbers, dashes, spaces, and parentheses
    const faxRegex = /^[0-9\s\-()]+$/;

    if (!faxRegex.test(value)) {
      return { invalidFax: true }; // Validation fails
    }

    return null; // Validation passes
  };
}