import { Routes } from '@angular/router';
import { StatsOverviewComponent } from './stats-overview/stats-overview.component';
import { StatsUpcomingEventsComponent } from './stats-upcoming-events/stats-upcoming-events.component';
import { StatsOnTheRiseComponent } from './stats-on-the-rise/stats-on-the-rise.component';
import { DancerPageComponent } from './dancer-page/dancer-page.component';
import { EventPageComponent } from './event-page/event-page.component';
import { DancersPageComponent } from './dancers-page/dancers-page.component';
import { EventsPageComponent } from './events-page/events-page.component';
import { AboutUsPageComponent } from './about-us-page/about-us-page.component';
import { DancersOverTimePageComponent } from './dancers-over-time-page/dancers-over-time-page.component';
import { DivisionProgressionPageComponent } from './division-progression-page/division-progression-page.component';

// WHEN ADDING BG, ALSO ADD TO INDEX.HTML FOR PRELOADING
const backgrounds = [
  "assets/img/swing_feet.jpg",
  "assets/img/swingfling.jpg",
  "assets/img/wcsroom.jpg",
  "assets/img/dip.jpg",
  "assets/img/swingout.jpg",
  "assets/img/jackandjill.jpg",
  "assets/img/swingdanceuk.jpg",
  "assets/img/lindy.jpg",
];

const linked_routes: Routes = [
  {
    path: '',
    component: StatsOverviewComponent,
  },
  {
    path: 'upcoming',
    component: StatsUpcomingEventsComponent,
  },
  {
    path: 'on-the-rise',
    component: StatsOnTheRiseComponent,
  },
  {
    path: 'dancers-over-time',
    component: DancersOverTimePageComponent,
  },
  {
    path: 'division-progression',
    component: DivisionProgressionPageComponent,
  },
  {
    path: 'about/us',
    component: AboutUsPageComponent,
  },
  {
    path: 'dancers',
    component: DancersPageComponent,
  },
  {
    path: 'events',
    component: EventsPageComponent,
  },
];

const __linked_routes = linked_routes.map((route, i, routes) => {
  route.data = {}
  if (i > 0) {
    route.data['previous'] = "/" + routes[i-1].path;
  }
  if (i < (routes.length - 1)) {
    route.data['next'] = "/" + routes[i+1].path;
  }
  route.data['bg'] = backgrounds[i % backgrounds.length];
  return route;
});

export const routes: Routes = [
  ...__linked_routes,
  { path: 'dancers/:id', component: DancerPageComponent, data: { bg: backgrounds[__linked_routes.length % backgrounds.length], previous: '_' } },
  { path: 'events/:id', component: EventPageComponent, data: { bg: backgrounds[(__linked_routes.length + 1) % backgrounds.length], previous: '_' } },
];
