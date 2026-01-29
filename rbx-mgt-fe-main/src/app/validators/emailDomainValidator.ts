import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';

export function emailDomainValidator(domain: string): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const email = control.value;
    if (!email) return null;

    // Check format: must have at least one character before the @ and match domain exactly
    const regex = new RegExp(`^[^@\\s]+${domain.replace('.', '\\.')}$`);

    return regex.test(email) ? null : { emailDomain: true };
  };
}