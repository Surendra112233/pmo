import { Directive ,ElementRef, HostListener, Self} from '@angular/core';
import { NgControl } from '@angular/forms';

@Directive({
  selector: '[appAlphanumeric]',
  standalone: true
})
export class AlphanumericDirective {

  constructor(private el: ElementRef,@Self() private control: NgControl) {}

  @HostListener('input', ['$event'])
  onInput(event: Event): void {
    const inputElement = this.el.nativeElement as HTMLInputElement;
    inputElement.value = inputElement.value.replace(/[^a-zA-Z0-9]/g, ''); // Replace non-alphanumeric characters
    this.control.control?.setValue(inputElement.value); // Update the form control
    this.control.control?.updateValueAndValidity(); // Trigger validation
  }

}

// Directive to allow alpha numeric and -, &, /
@Directive({
  selector: '[appAlphaNumericSpecialChars]',
  standalone: true
})
export class AlphaNumericSpecialCharsDirective {

  constructor(private ngControl: NgControl) {}

  @HostListener('input', ['$event']) onInputChange(event: Event) {
    const input = event.target as HTMLInputElement;
    
    // Remove any characters that are NOT a-z, A-Z, 0-9, -, &, /
    const cleaned = input.value.replace(/[^a-zA-Z0-9\-&\/ ]/g, '');

    if (input.value !== cleaned) {
      this.ngControl.control?.setValue(cleaned);
    }
  }
}

// Directive to allow alpha numeric with space
@Directive({
  selector: '[appAlphaNumericWithSpace]',
  standalone: true
})
export class AlphaNumericWithSpaceDirective {

  constructor(private ngControl: NgControl) {}

  @HostListener('input', ['$event']) onInputChange(event: Event) {
    const input = event.target as HTMLInputElement;

    const cleaned = input.value.replace(/[^a-zA-Z0-9 ]/g, '');

    if (input.value !== cleaned) {
      this.ngControl.control?.setValue(cleaned);
    }
  }
}

// Directive to allow emp code in format - RBX0000
@Directive({
  selector: '[appEmployeeCodeFormat]',
  standalone: true
})
export class EmployeeCodeFormatDirective {

  constructor(private el: ElementRef, private control: NgControl) {}

  @HostListener('input', ['$event'])
  onInput(event: any): void {
    let value: string = this.el.nativeElement.value.toUpperCase();

    // Allow only RBX followed by digits
    if (!/^RBX\d*$/.test(value)) {
      // Remove invalid parts
      value = value.replace(/[^0-9]/g, '');
      value = 'RBX' + value;
    }

    this.control.control?.setValue(value, { emitEvent: false });
  }
}
