import { Component, OnDestroy, OnInit } from '@angular/core';
import { Database, DatabaseFetcherService } from '../database-fetcher.service';

@Component({
  selector: 'app-stats-overview',
  standalone: true,
  imports: [],
  templateUrl: './stats-overview.component.html',
  styleUrl: './stats-overview.component.scss'
})
export class StatsOverviewComponent implements OnInit, OnDestroy {

  database: Database|undefined;
  is_loaded = false;

  constructor(private databaseFetcher: DatabaseFetcherService) {
    
  }
  ngOnDestroy(): void {
    this.is_loaded = false;
  }

  ngOnInit() {
    this.databaseFetcher.database.subscribe((db) => {
      this.database = db;
      this.is_loaded = true;
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
