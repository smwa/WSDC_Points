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


// WHEN ADDING BG, ALSO ADD TO INDEX.HTML FOR PRELOADING
export const routes: Routes = [
  { path: '', component: StatsOverviewComponent, data: { bg: "assets/img/swing_feet.jpg", next: '/upcoming' } },
  { path: 'upcoming', component: StatsUpcomingEventsComponent, data: { bg: "assets/img/swingfling.jpg", previous: '/', next: '/on-the-rise' } },
  { path: 'on-the-rise', component: StatsOnTheRiseComponent, data: { bg: "assets/img/wcsroom.jpg", previous: '/upcoming', next: '/dancers-over-time' } },
  { path: 'dancers-over-time', component: DancersOverTimePageComponent, data: { bg: "assets/img/wcsroom.jpg", previous: '/on-the-rise', next: '/about/us' } },
  { path: 'about/us', component: AboutUsPageComponent, data: { bg: "assets/img/jackandjill.jpg", previous: '/dancers-over-time', next: '/dancers' } },
  { path: 'dancers', component: DancersPageComponent, data: { bg: "assets/img/swingdanceuk.jpg", previous: '/about/us', next: '/events' } },
  { path: 'events', component: EventsPageComponent, data: { bg: "assets/img/swingout.jpg", previous: '/dancers' } },
  { path: 'dancers/:id', component: DancerPageComponent, data: { bg: "assets/img/dip.jpg", previous: '_' } },
  { path: 'events/:id', component: EventPageComponent, data: { bg: "assets/img/lindy.jpg", previous: '_' } },
];
