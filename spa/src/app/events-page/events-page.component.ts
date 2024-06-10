import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { RouterModule } from '@angular/router';
import { TemplateOneComponent } from '../template-one/template-one.component';
import { Database, DatabaseFetcherService } from '../database-fetcher.service';
import { StateService } from '../state.service';

@Component({
  selector: 'app-events-page',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    TemplateOneComponent,
  ],
  templateUrl: './events-page.component.html',
  styleUrl: './events-page.component.scss'
})
export class EventsPageComponent implements OnInit {
  database: Database|undefined;
  is_loaded = false;
  search = '';

  constructor(private databaseFetcher: DatabaseFetcherService, private stateService: StateService) { }

  ngOnInit() {
    this.is_loaded = false;
    this.databaseFetcher.database.subscribe((db) => {
      this.database = db;
      setTimeout(() => {
        this.search = this.stateService.eventsSearchField;
        this.is_loaded = true;
      }, 0)
    });
  }

  get_events() {
    if (!this.database) return [];
    if (this.search === '') return this.database.events.slice(0, 1000);
    return this.database.events.filter((event) => {
      const words = this.search.trim().split(' ');
      for (let word of words) {
        if (
          !event.name.toLowerCase().includes(word)
          && !event.location.toLowerCase().includes(word)
          && !event.id.toString().includes(word)
        ) {
          return false;
        }
      }
      return true;
    }).slice(0, 1000);
  }

  on_search_type(value: string) {
    this.search = value.toLowerCase();
    this.stateService.eventsSearchField = this.search;
  }

}
