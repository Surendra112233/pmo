import { Directive, ElementRef, HostListener, Self } from '@angular/core';
import { NgControl } from '@angular/forms';

@Directive({
  selector: '[appAllowOnlyChar]',
  standalone: true
})
export class AllowOnlyCharDirective {
  constructor(private el: ElementRef, @Self() private control: NgControl) {}

  @HostListener('input', ['$event'])
  onInput(event: Event): void {
    const inputElement = this.el.nativeElement as HTMLInputElement;
    inputElement.value = inputElement.value.replace(/[^a-zA-Z ]/g, ''); // Replace non-alphabet characters (allows spaces)
    this.control.control?.setValue(inputElement.value); // Update the form control
    this.control.control?.updateValueAndValidity(); // Trigger validation
  }

  // @HostListener('input', ['$event'])
  // onInput(event: Event): void {
  //   const inputElement = this.el.nativeElement as HTMLInputElement;

  //   // Remove non-alphabetic characters (allows spaces)
  //   let sanitizedValue = inputElement.value.replace(/[^a-zA-Z ]/g, '');

  //   if (sanitizedValue.length > 0) {
  //     sanitizedValue = sanitizedValue.charAt(0).toUpperCase() + sanitizedValue.slice(1);
  //   }

  //   this.control.control?.setValue(sanitizedValue);
  //   this.control.control?.updateValueAndValidity();
  // }
}
