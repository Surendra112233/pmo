import { CommonModule } from '@angular/common';
import { Component, Input, OnChanges, OnInit } from '@angular/core';
import { NgxGaugeModule } from 'ngx-gauge';

@Component({
  selector: 'app-manager-meter-gauge',
  templateUrl: './manager-meter-gauge.component.html',
  styleUrls: ['./manager-meter-gauge.component.scss'],
  standalone: true,
  imports: [CommonModule, NgxGaugeModule]
})
export class ManagerMeterGaugeComponent {
  @Input() percentage: number = 0;

  gaugeValue:any;
  thresholdConfig = {
    '0': {color: 'darkgreen'},
    '10': {color: 'darkgreen'},
    '20': {color: 'darkgreen'},
    '30': {color: 'darkgreen'},
    '40': {color: 'darkgreen'},
    '50': {color: 'darkgreen'},
    '60': {color: 'darkgreen'},
    '70': {color: '#66BB6A'},
    '80': {color: '#A5D6A7'},
    '85': {color: 'yellow'},
    '90': {color: 'lightcoral'},
    '95': {color: 'red'},
    '100': {color: 'red'}
};

  ngOnInit() {
    this.updateGauge
  }

  ngOnChanges() {
    this.updateGauge();
  }

  updateGauge() {
      this.gaugeValue = this.percentage;
  }
}
