import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class StateService {
  private _dancers_search_field: string = '';
  private _events_search_field: string = '';

  constructor() { }

  get dancersSearchField() {
    return this._dancers_search_field;
  }

  set dancersSearchField(value: string) {
    this._dancers_search_field = value;
  }

  get eventsSearchField() {
    return this._events_search_field;
  }

  set eventsSearchField(value: string) {
    this._events_search_field = value;
  }
}
