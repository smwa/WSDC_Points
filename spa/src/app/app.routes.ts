import { Routes } from '@angular/router';
import { StatsOverviewComponent } from './stats-overview/stats-overview.component';
import { StatsUpcomingEventsComponent } from './stats-upcoming-events/stats-upcoming-events.component';
import { StatsOnTheRiseComponent } from './stats-on-the-rise/stats-on-the-rise.component';
import { DancerPageComponent } from './dancer-page/dancer-page.component';
import { EventPageComponent } from './event-page/event-page.component';


// WHEN ADDING BG, ALSO ADD TO INDEX.HTML FOR PRELOADING
export const routes: Routes = [
  { path: '', component: StatsOverviewComponent, data: { bg: "assets/img/swing_feet.jpg", next: '/upcoming' } },
  { path: 'upcoming', component: StatsUpcomingEventsComponent, data: { bg: "assets/img/swingout.jpg", previous: '/', next: '/on-the-rise' } },
  { path: 'on-the-rise', component: StatsOnTheRiseComponent, data: { bg: "assets/img/courthouse.jpg", previous: '/upcoming' } },

  { path: 'dancers/:id', component: DancerPageComponent, data: { bg: "assets/img/courthouse.jpg", previous: '_' } },
  { path: 'events/:id', component: EventPageComponent, data: { bg: "assets/img/courthouse.jpg", previous: '_' } },
];
