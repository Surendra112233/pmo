import { Directive,HostListener } from '@angular/core';

@Directive({
  selector: '[appDisableKeys]',
  standalone: true
})
export class DisableKeysDirective {
  @HostListener('keydown', ['$event'])
  handleKeydown(event: KeyboardEvent): void {
    // Check if the key is Backspace or any of the Arrow keys
    const disabledKeys = ['Backspace', 'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'];
    if (disabledKeys.includes(event.key)) {
      event.preventDefault(); // Prevent the default action
    }
  }

}
