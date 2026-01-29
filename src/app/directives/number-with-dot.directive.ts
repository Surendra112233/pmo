import { Directive,HostListener } from '@angular/core';

@Directive({
  selector: '[appNumberWithDot]',
  standalone: true
})
export class NumberWithDotDirective {
  private regex: RegExp = new RegExp(/^[0-9]*\.?[0-9]*$/);
  private specialKeys: string[] = ['Backspace', 'Tab', 'End', 'Home', 'ArrowLeft', 'ArrowRight', 'Delete'];

  constructor() { }

  @HostListener('keydown', ['$event'])
  onKeyDown(event: KeyboardEvent): void {
    // Allow special keys
    if (this.specialKeys.includes(event.key)) {
      return;
    }

    // Prevent invalid keys
    const input = event.key;
    const current: string = (event.target as HTMLInputElement).value;
    const next: string = current.concat(input);

    if (!String(next).match(this.regex)) {
      event.preventDefault();
    }
  }

  @HostListener('paste', ['$event'])
  onPaste(event: ClipboardEvent): void {
    const clipboardData = event.clipboardData
    const pastedText = clipboardData?.getData('text') || '';
    if (!pastedText.match(this.regex)) {
      event.preventDefault();
    }
  }

}
