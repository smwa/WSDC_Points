import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { TemplateOneComponent } from '../template-one/template-one.component';
import { Database, DatabaseFetcherService } from '../database-fetcher.service';
import Chart from 'chart.js/auto';

@Component({
  selector: 'app-dancers-over-time-page',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    TemplateOneComponent,
  ],
  templateUrl: './dancers-over-time-page.component.html',
  styleUrl: './dancers-over-time-page.component.scss'
})
export class DancersOverTimePageComponent {
  database: Database|undefined;
  is_loaded = false;
  public chart: any;

  constructor(private databaseFetcher: DatabaseFetcherService) { }

  ngOnInit() {
    this.is_loaded = false;
    this.databaseFetcher.database.subscribe((db) => {
      this.database = db;
      setTimeout(() => {
        this.is_loaded = true;
        this.createChart();
      }, 0)
    });
  }


  createChart() {
    this.chart = new Chart("dot", {
      type: 'line',
      

      data: {
        labels: this.database?.new_dancers_over_time.map(t => t.key), 
	      datasets: [
          {
            label: "New Dancers With Points",
            data: this.database?.new_dancers_over_time.map(t => t.value),
            backgroundColor: 'black'
          }, 
        ]
      },
      options: {
        datasets: {
          line: {
            pointStyle: 'circle',
          },
        },
        elements: {
          line: {
            borderColor: 'white',
            backgroundColor: 'white',
          },
          point: {
            backgroundColor: 'white',
            borderColor: 'white',
          },
        },
        scales: {
          x: {
            ticks: {
              color: 'white',
            }
          },
          y: {
            ticks: {
              color: 'white',
            }
          }
        },
      },
      
    });
  }



}
