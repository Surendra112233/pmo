import { Component, Input, OnInit, ViewChild } from '@angular/core';
import { Chart } from 'chart.js';
import { ChartModule } from 'primeng/chart';
import ChartDataLabels from 'chartjs-plugin-datalabels';
import { ChartOptions, ChartType } from 'chart.js';
import { ToastModule } from 'primeng/toast';
import { ActivatedRouterService } from 'src/app/services/activated-router-service';
import { MessageService } from 'primeng/api';
import { DropdownModule } from 'primeng/dropdown';
import { FormBuilder, FormControl, FormGroup, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { Table, TableModule } from 'primeng/table';
import { CommonModule } from '@angular/common';
import { MasterDataService } from 'src/app/services/master-data.service';
import { Router } from '@angular/router';
import { MeterGaugeComponent } from './meter-gauge/meter-gauge.component';


//Initialize to display datalabels on bars
Chart.register(ChartDataLabels);



@Component({
  selector: 'app-employee-dashboard',
  templateUrl: './employee-dashboard.component.html',
  styleUrls: ['./employee-dashboard.component.scss'],
  imports: [ChartModule, ToastModule, DropdownModule, ReactiveFormsModule,
    TableModule, CommonModule, MeterGaugeComponent, FormsModule],
  standalone: true
})

export class EmployeeDashboardComponent implements OnInit{
  @ViewChild('dt2') dt : Table | undefined;

  years: { label: string; value: number }[] = [];
  selectedYear:any;
  barChartData: any;
  barChartOptions: any;
  apiResponse:any = [];
  dashboardForm!: FormGroup;
  employeeId:string='';
  tableData:any = [];
  pendingTableData:any = [];
  meterPercent:number = 0;

  // earliest fiscal start year that application has launched with
  earliestFiscalStart = 2025;

  animatedData = {
    targetUtilization: 0,
    targetUtilizationTillDate: 0,
    utilization: 0,
    totalUtilization: 0,
    totalUtilizationTillDate: 0
  };
  units = {
    targetUtilization: '',
    targetUtilizationTillDate: '',
    utilization: '',
    totalUtilization: '',
    totalUtilizationTillDate: '',
  };

  employeeDetails: any = {};
  showEmployeeInfo = true; // expanded by default

  constructor(
    private masterDataService: MasterDataService,
    private activatedRouterService: ActivatedRouterService,
    private messageService: MessageService,
    private fb: FormBuilder,
    private router: Router
  ){}
 
  ngOnInit() {
    this.employeeId = localStorage.getItem('userId') || '';

    // compute fiscal-year start (Apr - Mar). If month >= Apr, fiscal start is current year, else previous year.
    const now = new Date();
    const month = now.getMonth() + 1; // 1 to 12
    const currentFiscalStart = month >= 4 ? now.getFullYear() : now.getFullYear() - 1;

    // build fiscal year options (latest first)
    this.populateYearsRange(this.earliestFiscalStart, currentFiscalStart);

    // default selected fiscal start year
    this.selectedYear = currentFiscalStart;


    this.dashboardForm = this.fb.group({
      year: new FormControl(this.selectedYear)
    });

    // load data for default fiscal year
    this.getApiResponse();
  }  

  // Build list from earliest to current (latest first in dropdown)
  populateYearsRange(earliestStart: number, currentStart: number) {
    this.years = [];
    const start = Math.max(earliestStart, currentStart);

    // iterate from current down to earliest
    for (let y = currentStart; y >= earliestStart && y > 0; y--) {
      this.years.push({
        label: `${y}-${(y + 1).toString().slice(-2)}`, // e.g., "2025-26"
        value: y
      });
    }
    
    // if no years were added (unlikely), add current as fallback
    if (this.years.length === 0) {
      this.years.push({
        label: `${currentStart}-${(currentStart + 1).toString().slice(-2)}`,
        value: currentStart
      });
    }
  }

  toggleEmployeeInfo() {
    this.showEmployeeInfo = !this.showEmployeeInfo;
  }

  getDashboardData(event?:any){
    // this.selectedYear=event.value;
    if (event && event.value !== undefined) {
      this.selectedYear = event.value;
      this.dashboardForm.get('year')?.setValue(this.selectedYear, { emitEvent: false });
    } else {
      this.selectedYear = this.dashboardForm.get('year')?.value;
    }
    this.getApiResponse();
  }

  getApiResponse() {
    this.masterDataService.getDashboardResponse(this.selectedYear, this.employeeId).subscribe((res:any)=>{
      this.apiResponse = res;
      this.genarateUtilizationTable();
      this.genarateMeterGauge();
      this.genarateBarChart();
      this.genratePendingTable();
      this.employeeDetails = res.employeeDetails || {
        name: 'N/A',
        band: 'N/A',
        reportingManager: 'N/A',
        joiningDate: '',
        department: 'N/A'
      };
    }, (err:any) => {
        this.activatedRouterService.updateError(err, this.messageService);
    })
  }

  genarateUtilizationTable() {
    this.tableData = this.apiResponse.tableData;
    // this.tableData = [this.apiResponse.tableData];

    // Extract numeric values and units
    this.extractAndAnimate(this.apiResponse.tableData);
  }

  extractAndAnimate(data: any) {
    Object.keys(data).forEach((key) => {
      const typedKey = key as keyof typeof this.animatedData; // cast here
      const match = data[key].match(/^([\d.]+)\s*(.*)$/);
      if (match) {
        const numericValue = parseFloat(match[1]);
        this.units[typedKey] = match[2]; // set unit like 'hours' or '%'
        this.animateValue(typedKey, numericValue);
      }
    });
  }
  
  animateValue(field: keyof typeof this.animatedData, target: number) {
    let step = 0;
    const duration = 1000;
    const frameRate = 20;
    const steps = duration / frameRate;
    const increment = target / steps;
  
    const interval = setInterval(() => {
      step++;
      this.animatedData[field] += increment;
      if (step >= steps) {
        this.animatedData[field] = target;
        clearInterval(interval);
      }
    }, frameRate);
  }

  genarateMeterGauge() {
    this.meterPercent = this.apiResponse.meterData.percentageTillDate;    
  }

  genarateBarChart() {
    this.barChartData = {
      labels: this.apiResponse.chartData.labels,
      datasets: [
        {
          label: 'Values',
          // data: this.apiResponse.chartData.data,
          data: this.apiResponse.chartData.data.map((item:any) => parseInt(item.split(' ')[0], 10)), // only numbers for the bar chart
          backgroundColor: [
            '#FFA726', '#42A5F5', '#42A5F5', '#42A5F5',
            '#FFA726', '#42A5F5', '#42A5F5', '#42A5F5',
            '#FFA726', '#42A5F5', '#42A5F5', '#42A5F5',
            '#FFA726', '#42A5F5', '#42A5F5', '#42A5F5'
          ],
          barThickness: 18,
          // borderRadius: 50
        }
      ]
    };    
    // this.barChartData = {
    //   labels: [
    //     'Q1 Total', 'Apr'+' '+this.selectedYear, 'May'+' '+this.selectedYear, 'Jun'+' '+ this.selectedYear,
    //     'Q2 Total', 'Jul'+' '+ this.selectedYear, 'Aug'+' '+ this.selectedYear, 'Sep'+' '+ this.selectedYear,
    //     'Q3 Total', 'Oct'+' '+ this.selectedYear, 'Nov'+' '+ this.selectedYear, 'Dec'+' '+ this.selectedYear,
    //     'Q4 Total', 'Jan'+' '+ (this.selectedYear+1), 'Feb'+' '+ (this.selectedYear+1), 'Mar'+' '+ (this.selectedYear+1)
    //   ],
    //   datasets: [
    //     {
    //       label: 'Values',
    //       data: [65, 20, 25, 20, 90, 30, 30, 30, 85, 25, 30, 30, 75, 20, 25, 30],
    //       backgroundColor: [
    //         '#FFA726', '#42A5F5', '#42A5F5', '#42A5F5',
    //         '#FFA726', '#42A5F5', '#42A5F5', '#42A5F5',
    //         '#FFA726', '#42A5F5', '#42A5F5', '#42A5F5',
    //         '#FFA726', '#42A5F5', '#42A5F5', '#42A5F5'
    //       ]
    //     }
    //   ]
    // };
 
    this.barChartOptions = {
      indexAxis: 'y', // Horizontal bars
      responsive: true,
      // animation: false,
      animation: {
        duration: 1000, // Animation duration in ms
        easing: 'easeOutQuart', // Smooth easing
      },
      plugins: {
        legend: {
          display: false
        },
        // tooltip: {
        //  // mode: 'index',
        //   intersect: true
        // },
        tooltip: {
          callbacks: {
            label: (context: any) => {
              // Return the raw value with percentage from your API response
              return this.apiResponse.chartData.data[context.dataIndex];
            }
          }
        },
        datalabels: {
          anchor: 'end',
          align: 'right',
          // anchor: 'center',
          // align: 'center',
          color: '#000',
          font: {
            weight: 'bold'
          },
          formatter: (_value: number, context: any) => {
            const label = this.apiResponse.chartData.data[context.dataIndex];
            // return label.includes('0') ? '' : label;
            return label.includes('(0%)') ? '' : label;
            // return label;
          }
          // formatter: (value: number) => value === 0 ? '' : `${value}`
          // formatter: (value: number) => value === 0 ? '' : `${value}%`
        }
      },
      scales: {
        x: {
          beginAtZero: true
        },
        y: {
          ticks: {
            autoSkip: false,
            font: (ctx: any) => {
              const label = ctx.tick.label;
              return {
                weight: ['Q1', 'Q2', 'Q3', 'Q4'].includes(label) ? 'bold' : 'normal',
                size: 12
              };
            }
          }
        }
      }
    };
  }

  genratePendingTable() {
    this.pendingTableData = this.apiResponse.pendingData;
  }

  applyFilterGlobal($event:any, stringVal:any) {
    this.dt!.filterGlobal(($event.target as HTMLInputElement).value, stringVal);
  }

  addTimesheet() {
    this.router.navigate(['/emp/add_timesheet']);
  }

}
