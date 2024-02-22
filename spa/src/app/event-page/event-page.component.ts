import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { TemplateOneComponent } from '../template-one/template-one.component';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { Event, Database, DatabaseFetcherService } from '../database-fetcher.service';

@Component({
  selector: 'app-event-page',
  standalone: true,
  imports: [
    CommonModule,
    TemplateOneComponent,
    RouterModule,
  ],
  templateUrl: './event-page.component.html',
  styleUrl: './event-page.component.scss'
})
export class EventPageComponent implements OnInit {
  database: Database|undefined;
  is_loaded = false;
  event: undefined|Event = undefined;
  event_id: undefined|number = undefined;

  constructor(private databaseFetcher: DatabaseFetcherService, private route: ActivatedRoute) {
  }

  ngOnInit() {
    this.is_loaded = false;
    this.event = undefined;


    this.route.params.subscribe(
      params => {
        this.event_id = parseInt(params['id'], 10);
        this.event = this.database?.events.filter((_event) => _event.id == this.event_id)[0];
      }
    );


    this.databaseFetcher.database.subscribe((db) => {
      this.database = db;
      this.event = this.database?.events.filter((_event) => _event.id == this.event_id)[0];
      setTimeout(() => {
        this.is_loaded = true;
      }, 0)
    });
  }

}
