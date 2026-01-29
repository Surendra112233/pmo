import { CommonModule } from '@angular/common';
import { Component, Input, OnChanges, OnInit } from '@angular/core';
import { NgxGaugeModule } from 'ngx-gauge';

@Component({
  selector: 'app-meter-gauge',
  templateUrl: './meter-gauge.component.html',
  styleUrls: ['./meter-gauge.component.scss'],
  standalone: true,
  imports: [CommonModule, NgxGaugeModule]
})
export class MeterGaugeComponent implements OnInit {
// export class MeterGaugeComponent implements OnInit, OnChanges {
  @Input() percentage: number = 0;
  // pointerX = 0;
  // pointerY = 0;
  // ticks: any[] = [];

  gaugeValue:any;
  thresholdConfig = {
    '0': {color: 'crimson'},
    '10': {color: 'red'},
    '20': {color: 'red'},
    '30': {color: 'red'},
    '40': {color: 'red'},
    '50': {color: 'red'},
    '60': {color: 'red'},
    '70': {color: 'lightcoral'},
    '80': {color: 'yellow'},
    '85': {color: '#A5D6A7'}, /* #A5D6A7 Light Green */
    '90': {color: '#66BB6A'}, /* #66BB6A Medium Green */
    '95': {color: 'darkgreen'}, /* #556B2F Dark Olive Green */
    '100': {color: 'darkgreen'} 
};

  ngOnInit() {
    this.updateGauge
  }

  ngOnChanges() {
    this.updateGauge();
    // this.updatePointer();
  }

  updateGauge() {
      this.gaugeValue = this.percentage;
  }


  // ngOnInit() {
  //   this.ticks = this.generateTicks();
  //   this.updatePointer();
  // }



  // private polarToCartesian(centerX: number, centerY: number, radius: number, angleDegrees: number) {
  //   const angleRadians = (angleDegrees - 90) * Math.PI / 180.0;
  //   return {
  //     x: centerX + radius * Math.cos(angleRadians),
  //     y: centerY + radius * Math.sin(angleRadians)
  //   };
  // }

  // private describeArc(x: number, y: number, radius: number, startAngle: number, endAngle: number) {
  //   const start = this.polarToCartesian(x, y, radius, endAngle);
  //   const end = this.polarToCartesian(x, y, radius, startAngle);
  //   const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1";

  //   return [
  //     "M", start.x, start.y,
  //     "A", radius, radius, 0, largeArcFlag, 0, end.x, end.y
  //   ].join(" ");
  // }

  // updatePointer() {
  //   const angle = 135 + (this.percentage / 100) * 270;
  //   const rad = angle * Math.PI / 180;
  //   this.pointerX = 50 + Math.cos(rad) * 35;
  //   this.pointerY = 50 + Math.sin(rad) * 35;
  // }

  // generateTicks() {
  //   const ticks = [];
  //   for (let i = 0; i <= 100; i += 10) {
  //     const angle = 135 + (i / 100) * 270;
  //     const rad = angle * Math.PI / 180;

  //     const x1 = 50 + Math.cos(rad) * 40;
  //     const y1 = 50 + Math.sin(rad) * 40;
  //     const x2 = 50 + Math.cos(rad) * 35;
  //     const y2 = 50 + Math.sin(rad) * 35;
  //     const lx = 50 + Math.cos(rad) * 30;
  //     const ly = 50 + Math.sin(rad) * 30;

  //     ticks.push({ x1, y1, x2, y2, lx, ly, label: i });
  //   }
  //   return ticks;
  // }

  // getArcPath(start: number, end: number) {
  //   return this.describeArc(50, 50, 40, 135 + (start / 100) * 270, 135 + (end / 100) * 270);
  // }
}