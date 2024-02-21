import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { TemplateOneComponent } from '../template-one/template-one.component';
import { Database, DatabaseFetcherService } from '../database-fetcher.service';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-stats-upcoming-events',
  standalone: true,
  imports: [
    CommonModule,
    TemplateOneComponent,
    RouterModule,
  ],
  templateUrl: './stats-upcoming-events.component.html',
  styleUrl: './stats-upcoming-events.component.scss'
})
export class StatsUpcomingEventsComponent implements OnInit {
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

  get_event_by_id(event_id: number) {
    return this.database?.events.filter((_event) => _event.id == event_id)[0];
  }

  get_events() {
    if (!this.database) return [];
    var events = this.database.past_events_that_may_be_recurring.map(e => this.get_event_by_id(e)).filter(e => e !== undefined);
    return events;
  }
}
