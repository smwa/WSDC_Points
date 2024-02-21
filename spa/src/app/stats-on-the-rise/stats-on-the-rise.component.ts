import { Component, OnInit } from '@angular/core';
import { Database, DatabaseFetcherService } from '../database-fetcher.service';
import { TemplateOneComponent } from '../template-one/template-one.component';
import { RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-stats-on-the-rise',
  standalone: true,
  imports: [
    RouterModule,
    TemplateOneComponent,
    CommonModule,
  ],
  templateUrl: './stats-on-the-rise.component.html',
  styleUrl: './stats-on-the-rise.component.scss'
})
export class StatsOnTheRiseComponent implements OnInit {
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

  onTheRise() {
    if (typeof this.database == undefined) return [];
    const ret = [];

    return this.database?.top_dancers_by_points_gained_recently;
  }

  get_dancer(_id: number) {
    const dancer = this.database?.dancers.filter((_dancer) => _dancer.id == _id)[0];
    if (dancer == undefined) throw new Error('Dancer does not exist');
    return dancer;
  }

  get_role(_id: number) {
    return this.database?.roles[_id];
  }

  get_division(_id: number) {
    return this.database?.divisions[_id];
  }
}
