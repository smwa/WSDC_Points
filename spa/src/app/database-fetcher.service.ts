import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { decode, decodeAsync } from "@msgpack/msgpack";
import { map, Observer, Observable } from 'rxjs';

declare global {
  interface Window {
      database: any;
  }
}

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
  primary_role: number,
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

export type Dancer = {
  id: number,
  pro: boolean,
  primary_role: number,
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

export type Event = {
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
  new_dancers_over_time: {key: string, value: number}[],
  ordered_skill_divisions: number[],
};

export type Database = {
  last_updated: Date,
  roles: {[id: string]: string},
  divisions: {[id: string]: string},
  dancers: Dancer[],
  events: Event[],
  top_dancers_by_points_gained_recently: {division: number, roles: {role: number, dancers: {points: number, wscdid: number}[]}[]}[],
  past_events_that_may_be_recurring: number[],
  new_dancers_over_time: {key: string, value: number}[],
  ordered_skill_divisions: number[],
};

@Injectable({
  providedIn: 'root'
})
export class DatabaseFetcherService {
  
  private fetch_database = () => {
    return this.http.get<ArrayBuffer>('assets/database.txt', { responseType: 'arraybuffer' as 'json', observe: 'response' }).pipe(map((_database) => {

      if (_database.body == null) return;

      const database = decode(_database.body) as IncomingDatabase;
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
      console.log("Setting window.database, so you can dig into the data");
      window.database = db;
      return db;
    }));
  }

  public database: Observable<Database>;

  constructor(private http: HttpClient) {
    this.database = new Observable<Database>(observer => {

      navigator.serviceWorker.addEventListener('message', (event) => {
        if(event.data.type == "fetched" && event.data.url.indexOf("database") >= 0) {
          this.fetch_database().subscribe((db) => {
            observer.next(db);
          });
        }
      });

      this.fetch_database().subscribe((db) => {
        observer.next(db);
      });

    });
  }

}
