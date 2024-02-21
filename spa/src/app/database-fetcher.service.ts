import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { map } from 'rxjs';

type IncomingEvent = {
  id: number,
  name: string,
  location: string,
  url: string,
  dates: string[],
};

type IncomingDancer = {
  id: number,
  pro: boolean,
  first: string,
  last: string,
  placements: {
    role: number,
    result: string,
    points: number,
    event: number,
    date: string,
    division: number,
  }[],
};

type Dancer = {
  id: number,
  pro: boolean,
  first: string,
  last: string,
  placements: {
    role: number,
    result: string,
    points: number,
    event: number,
    date: Date,
    division: number,
  }[],
};

type Event = {
  id: number,
  name: string,
  location: string,
  url: string,
  dates: Date[],
};

type IncomingDatabase = {
  last_updated: string,
  roles: {[id: string]: string},
  divisions: {[id: string]: string},
  dancers: IncomingDancer[],
  events: IncomingEvent[],
  top_dancers_by_points_gained_recently: {division: number, roles: {role: number, dancers: {points: number, wscdid: number}[]}[]}[],
  past_events_that_may_be_recurring: number[],
};

export type Database = {
  last_updated: Date,
  roles: {[id: string]: string},
  divisions: {[id: string]: string},
  dancers: Dancer[],
  events: Event[],
  top_dancers_by_points_gained_recently: {division: number, roles: {role: number, dancers: {points: number, wscdid: number}[]}[]}[],
  past_events_that_may_be_recurring: number[],
};

@Injectable({
  providedIn: 'root'
})
export class DatabaseFetcherService {

  database = this.http.get<IncomingDatabase>('assets/database.json').pipe(map((database) => {
    const db: Database = {
      ...database,
      last_updated: new Date(database.last_updated),
      events: database.events.map((old_event) => ({
        ...old_event,
        dates: old_event.dates.map(d => new Date(d)),
      })),
      dancers: database.dancers.map((old_dancer) => ({
        ...old_dancer,
        placements: old_dancer.placements.map(old_placement => ({
          ...old_placement,
          date: new Date(old_placement.date),
        })),
      })),
    }
    return db;
  }));

  constructor(private http: HttpClient) { }

}
