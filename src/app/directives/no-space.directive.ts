import { Directive, HostListener, ElementRef, Self } from '@angular/core';
import { NgControl } from '@angular/forms';

@Directive({
  selector: '[appNoSpace]',
  standalone: true
})
export class NoSpaceDirective {

  constructor(private el: ElementRef, @Self() private control: NgControl) {}

  // @HostListener('input', ['$event']) onInputChange(event: Event): void {
  //   const input = this.el.nativeElement;    
  //   let value = input.value;
  //   value = value.trim();
  //   value = value.replace(/\s+/g, ' ');
  //   input.value = value;
  // }

  @HostListener('input', ['$event']) onInputChange(event: Event): void {
    const input = this.el.nativeElement;
    let value = input.value;
    value = value.replace(/^\s+/, ''); 

    value = value.replace(/\s{2,}/g, ' ');

    if (value.endsWith(' ')) {
      value = value.trimEnd() + ' '; 
    }
    input.value = value;
  }
}
