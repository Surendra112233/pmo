import {
    Directive,
    ElementRef,
    Input,
    Renderer2,
    HostListener,
    OnInit
  } from '@angular/core';
  
  @Directive({
    selector: '[appTooltip]',
    standalone: true
  })
  export class TooltipDirective implements OnInit {
    @Input('appTooltip') tooltipLabel: string = '';
    @Input() position: 'top' | 'bottom' | 'left' | 'right' = 'top';
  
    private tooltipElement: HTMLElement | null = null;
  
    constructor(private el: ElementRef, private renderer: Renderer2) {}
  
    ngOnInit() {
      this.renderer.setStyle(this.el.nativeElement, 'position', 'relative');
      this.renderer.setStyle(this.el.nativeElement, 'cursor', 'pointer');
    }
  
    @HostListener('mouseenter') onMouseEnter() {
      this.showTooltip();
    }
  
    @HostListener('mouseleave') onMouseLeave() {
      this.hideTooltip();
    }
  
    private showTooltip() {
      if (this.tooltipElement) return;
  
      this.tooltipElement = this.renderer.createElement('span');
      this.renderer.appendChild(
        this.tooltipElement,
        this.renderer.createText(this.tooltipLabel)
      );
  
      this.renderer.appendChild(this.el.nativeElement, this.tooltipElement);
  
      this.renderer.setStyle(this.tooltipElement, 'position', 'absolute');
      this.renderer.setStyle(this.tooltipElement, 'padding', '8px 10px');
    //   this.renderer.setStyle(this.tooltipElement, 'background', '#f3f3f9'); //dark blue
    //   this.renderer.setStyle(this.tooltipElement, 'background', '#abb9e8'); //light blue
      this.renderer.setStyle(this.tooltipElement, 'background', '#fff');
      this.renderer.setStyle(this.tooltipElement, 'color', '#000');
      this.renderer.setStyle(this.tooltipElement, 'border', '1px solid #000');
      this.renderer.setStyle(this.tooltipElement, 'border-radius', '4px');
      this.renderer.setStyle(this.tooltipElement, 'font-size', '12px');
      this.renderer.setStyle(this.tooltipElement, 'z-index', '1000');
      this.renderer.setStyle(this.tooltipElement, 'white-space', 'nowrap');
      this.renderer.setStyle(this.tooltipElement, 'font-family', 'Poppins, sans-serif');
      this.renderer.setStyle(this.tooltipElement, 'font-weight', 'normal');
  
      const position = this.calculatePosition();
      Object.entries(position).forEach(([key, value]) =>
        this.renderer.setStyle(this.tooltipElement!, key, value)
      );
    }
  
    private hideTooltip() {
      if (this.tooltipElement) {
        this.renderer.removeChild(this.el.nativeElement, this.tooltipElement);
        this.tooltipElement = null;
      }
    }
  
    private calculatePosition(): { [key: string]: string } {
      const hostRect = this.el.nativeElement.getBoundingClientRect();
      const tooltipRect = this.tooltipElement?.getBoundingClientRect();
  
      switch (this.position) {
        case 'top':
          return {
            bottom: `${hostRect.height}px`,
            left: `${(hostRect.width - (tooltipRect?.width || 0)) / 2}px`
          };
        case 'bottom':
          return {
            top: `${hostRect.height}px`,
            left: `${(hostRect.width - (tooltipRect?.width || 0)) / 2}px`
          };
        case 'left':
          return {
            top: `${(hostRect.height - (tooltipRect?.height || 0)) / 2}px`,
            right: `${hostRect.width}px`
          };
        case 'right':
          return {
            top: `${(hostRect.height - (tooltipRect?.height || 0)) / 2}px`,
            left: `${hostRect.width}px`
          };
        default:
          return {};
      }
    }
  }  