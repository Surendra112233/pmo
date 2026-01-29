import { Directive, HostListener, ElementRef } from '@angular/core';

@Directive({
  selector: '[appNoSpecialChars]',
  standalone: true
})
export class NoSpecialCharsDirective {
  private regex: RegExp = /[#\$^\*\(\)]/; // Define restricted characters

  constructor(private el: ElementRef) {}

  @HostListener('keypress', ['$event']) onKeyPress(event: KeyboardEvent) {
    if (this.regex.test(event.key)) {
      event.preventDefault(); // Block the character from being typed
    }
  }

  @HostListener('input', ['$event']) onInput(event: any) {
    const initialValue = this.el.nativeElement.value;
    this.el.nativeElement.value = initialValue.replace(this.regex, ''); // Remove invalid characters
    if (initialValue !== this.el.nativeElement.value) {
      event.stopPropagation(); // Prevent further event propagation
    }
  }
}