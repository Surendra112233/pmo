import { Directive, HostListener } from '@angular/core';
import { NgControl } from '@angular/forms';

@Directive({
  selector: '[appAlphanumericSpecial]',
  standalone: true
})
export class AlphanumericSpecialDirective {

  // Regex to allow alphanumeric and specific special characters
  private regex: RegExp = /^[a-zA-Z0-9'&./\-_ ]*$/;

  constructor(private control: NgControl) {}

  @HostListener('input', ['$event'])
  onInputChange(event: Event): void {
    const inputElement = event.target as HTMLInputElement;
    const value = inputElement.value;

    // Replace invalid characters
    const filteredValue = value.split('').filter(char => this.regex.test(char)).join('');
    
    if (value !== filteredValue) {
      this.control.control?.setValue(filteredValue);
    }
  }

}
