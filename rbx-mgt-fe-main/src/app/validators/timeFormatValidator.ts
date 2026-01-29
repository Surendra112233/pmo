import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';

export function timeFormatValidator(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const value = control.value;

    // If the field is empty, validation passes (use required validator for non-empty checks)
    if (!value) {
      return null;
    }

    // Regex to validate HH:mm format (24-hour clock)
    const timeRegex = /^([01]\d|2[0-3]):([0-5]\d)$/;

    if (!timeRegex.test(value)) {
      return { invalidTimeFormat: true }; // Validation fails
    }

    return null; // Validation passes
  };
}