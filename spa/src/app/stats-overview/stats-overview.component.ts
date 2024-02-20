import { Component, OnInit } from '@angular/core';
import { Database, DatabaseFetcherService } from '../database-fetcher.service';
import { CommonModule } from '@angular/common';
import { TemplateOneComponent } from '../template-one/template-one.component';

@Component({
  selector: 'app-stats-overview',
  standalone: true,
  imports: [
    CommonModule,
    TemplateOneComponent
  ],
  templateUrl: './stats-overview.component.html',
  styleUrl: './stats-overview.component.scss'
})
export class StatsOverviewComponent implements OnInit {

  database: Database|undefined;
  is_loaded = false;

  constructor(private databaseFetcher: DatabaseFetcherService) { }

  ngOnInit() {
    this.is_loaded = false;
    this.databaseFetcher.database.subscribe((db) => {
      this.database = db;
      setTimeout(() => {
        this.is_loaded = true;
      }, 0)
    });
  }

  get_last_updated() {
    if (typeof this.database == undefined) return '';
    return this.database?.last_updated.toLocaleDateString('en-US', {month: 'long', day: 'numeric', year: 'numeric'});
  }

  get_number_of_dancers() {
    if (!this.database) return '';
    return '' + Object.entries(this.database?.dancers).length;
  }

  get_number_of_events() {
    if (!this.database) return '';
    return '' + Object.entries(this.database?.events).length;
  }
}
