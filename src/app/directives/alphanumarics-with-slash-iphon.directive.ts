import { Directive, ElementRef, HostListener, Self } from '@angular/core';
import { NgControl } from '@angular/forms';

@Directive({
  selector: '[appAlphanumaricsWithSlashIphon]',
  standalone: true
})
export class AlphanumaricsWithSlashIphonDirective {
  constructor(private el: ElementRef, @Self() private control: NgControl) {}

  @HostListener('input', ['$event'])
  onInput(event: Event): void {
    const inputElement = this.el.nativeElement as HTMLInputElement;

    let sanitizedValue = inputElement.value.replace(/[^a-zA-Z0-9 /_-]/g, '');

    // Ensure the first letter is capitalized
    if (sanitizedValue.length > 0) {
      sanitizedValue = sanitizedValue.charAt(0).toUpperCase() + sanitizedValue.slice(1);
    }
    // Set the updated value
    this.control.control?.setValue(sanitizedValue); 
    this.control.control?.updateValueAndValidity();
  }
}
