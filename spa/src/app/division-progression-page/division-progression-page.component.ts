import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { TemplateOneComponent } from '../template-one/template-one.component';
import { Database, DatabaseFetcherService } from '../database-fetcher.service';
import { BoxPlotChart, IBoxAndWhiskersOptions } from '@sgratzl/chartjs-chart-boxplot';
import { _DeepPartialObject } from 'chart.js/dist/types/utils';

@Component({
  selector: 'app-division-progression-page',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    TemplateOneComponent,
  ],
  templateUrl: './division-progression-page.component.html',
  styleUrl: './division-progression-page.component.scss'
})
export class DivisionProgressionPageComponent {
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
    const ONE_DAY_IN_MS = 24 * 60 * 60 * 1000;

    const divisions_plus_top = this.database?.ordered_skill_divisions || [];
    const data_all_by_key: {[id: number]: number[]} = {};

    this.database?.dancers.forEach(dancer => {
      const earliest_date_by_division: {[id: number]: Date} = {};

      dancer.placements
        .filter(p => p.role === dancer.primary_role)
        .forEach(placement => {
          if (!(placement.division in earliest_date_by_division)) {
            earliest_date_by_division[placement.division] = placement.date;
          }
          else {
            if (placement.date < earliest_date_by_division[placement.division]) {
              earliest_date_by_division[placement.division] = placement.date;
            }
          }
        });

        for (let i = 1; i < divisions_plus_top.length; i++) {
          const from_division = divisions_plus_top[i-1];
          const to_division = divisions_plus_top[i];
          if (!(from_division in earliest_date_by_division) || !(to_division in earliest_date_by_division)) {
            continue;
          }
          const from_division_date = earliest_date_by_division[from_division];
          const to_division_date = earliest_date_by_division[to_division];
          const days = Math.round(Math.abs((to_division_date.getTime() - from_division_date.getTime()) / ONE_DAY_IN_MS))
          if (!(from_division in data_all_by_key)) {
            data_all_by_key[from_division] = [];
          }
          data_all_by_key[from_division].push(days);
        }

    });


    const data_all: number[][] = [];
    const labels = [];
    
    for (let i = 1; i < divisions_plus_top.length; i++) {
      const from_division = divisions_plus_top[i-1];
      const to_division = divisions_plus_top[i];
      labels.push(this.database?.divisions[from_division]);
      data_all.push(data_all_by_key[from_division]);
    }

    const options: IBoxAndWhiskersOptions = {
      meanRadius: 0,
      medianColor: '',
      lowerBackgroundColor: '',
      backgroundColor: '',
      borderColor: '',
      borderWidth: 0,
      outlierStyle: 'circle',
      outlierRadius: 2,
      outlierBackgroundColor: '#CCCCCC',
      outlierBorderColor: '',
      outlierBorderWidth: 0,
      itemStyle: 'line',
      itemRadius: 0,
      itemBackgroundColor: '',
      itemBorderColor: '',
      itemBorderWidth: 0,
      hitPadding: 0,
      outlierHitRadius: 0,
      meanStyle: 'line',
      meanBackgroundColor: '',
      meanBorderColor: '',
      meanBorderWidth: 0
    }

    this.chart = new BoxPlotChart("dp", {      

      data: {
        labels: labels,
	      datasets: [
          {
            minStats: 'min',
            maxStats: 'whiskerMax',
            label: "All",
            data: data_all,
          }, 
        ]
      },

      options: options,
      
    });
  }



}
