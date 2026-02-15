import { Directive, Input, HostListener, Renderer2 } from '@angular/core';
import { AbstractControl, ValidationErrors } from '@angular/forms';

@Directive({
  selector: '[appValidateTotal]',
  standalone: true
})
export class ValidateTotalDirective {

  @Input() field1: number = 0;
  @Input() field2: number = 0;
  @Input() totalPatientsControl: AbstractControl | null = null;

  constructor(private renderer: Renderer2) {}

  // Custom validation logic
  validateTotal(): ValidationErrors | null {
    const sum = this.field1 + this.field2;
    if (this.totalPatientsControl && this.totalPatientsControl.value !== sum) {
      return { totalMismatch: true }; // Error if sum doesn't match totalPatients
    }
    return null;
  }

  // Listen to input changes to trigger validation
  @HostListener('input', ['$event'])
  onInputChange() {
    if (this.totalPatientsControl) {
      const error = this.validateTotal();
      if (error) {
        this.totalPatientsControl.setErrors(error);
      } else {
        this.totalPatientsControl.setErrors(null);
      }
    }
  }
}
