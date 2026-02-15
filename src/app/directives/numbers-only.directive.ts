import { Directive, HostListener } from '@angular/core';

@Directive({
  selector: '[appNumbersOnly]',
  standalone: true,
})
export class NumbersOnlyDirective {
  @HostListener('input', ['$event']) onInput(event: Event) {
    const input = event.target as HTMLInputElement;
    input.value = input.value.replace(/[^0-9]/g, ''); // Remove non-numeric characters
    input.dispatchEvent(new Event('input')); // Trigger input event for Angular binding
  }

  @HostListener('keydown', ['$event']) onKeyDown(event: KeyboardEvent) {
    // Allow navigation keys and basic controls
    if (
      [
        'Backspace', 'Tab', 'Escape', 'Enter', 'ArrowLeft', 'ArrowRight',
        'ArrowUp', 'ArrowDown'
      ].includes(event.key)
    ) {
      return;
    }

    // Allow Ctrl+A, Ctrl+C, Ctrl+X, Ctrl+V (Paste)
    if ((event.ctrlKey || event.metaKey) && ['a', 'c', 'x', 'v'].includes(event.key.toLowerCase())) {
      return;
    }

    // Allow numbers only
    if (!/^[0-9]$/.test(event.key)) {
      event.preventDefault();
    }
  }
}

@Directive({
  selector: '[appMobileNumbersOnly]',
  standalone: true,
})
export class MobileNumbersOnlyDirective {

  @HostListener('input', ['$event']) onInput(event: Event) {
    const input = event.target as HTMLInputElement;

    // Allow digits, +, and -
    input.value = input.value.replace(/[^0-9+\- ]/g, '');
    input.dispatchEvent(new Event('input')); // Trigger input event for Angular binding
  }

  @HostListener('keydown', ['$event']) onKeyDown(event: KeyboardEvent) {
    // Allow navigation and control keys
    if (
      [
        'Backspace', 'Tab', 'Escape', 'Enter',
        'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'
      ].includes(event.key)
    ) {
      return;
    }

    // Allow Ctrl+A, Ctrl+C, Ctrl+X, Ctrl+V
    if ((event.ctrlKey || event.metaKey) && ['a', 'c', 'x', 'v'].includes(event.key.toLowerCase())) {
      return;
    }

    // Allow numbers, +, and -
    if (!/^[0-9+\- ]$/.test(event.key)) {
      event.preventDefault();
    }
  }
}