import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { RouterModule } from '@angular/router';
import { TemplateOneComponent } from '../template-one/template-one.component';
import { Database, DatabaseFetcherService } from '../database-fetcher.service';

@Component({
  selector: 'app-dancers-page',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    TemplateOneComponent,
  ],
  templateUrl: './dancers-page.component.html',
  styleUrl: './dancers-page.component.scss'
})
export class DancersPageComponent implements OnInit {
  database: Database|undefined;
  is_loaded = false;
  search = '';

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

  get_dancers() {
    if (!this.database) return [];
    if (this.search === '') return this.database.dancers.slice(0, 1000);
    return this.database.dancers.filter((dancer) => {
      const words = this.search.trim().split(' ');
      for (let word of words) {
        if (
          !dancer.first.toLowerCase().includes(word)
          && !dancer.last.toLowerCase().includes(word)
          && !dancer.id.toString().includes(word)
        ) {
          return false;
        }
      }
      return true;
    }).slice(0, 1000); // TODO
  }

  on_search_type(value: string) {
    this.search = value.toLowerCase();
    console.log(this.search);
  }

}
