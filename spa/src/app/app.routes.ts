import { Routes } from '@angular/router';
import { StatsOverviewComponent } from './stats-overview/stats-overview.component';
import { StatsUpcomingEventsComponent } from './stats-upcoming-events/stats-upcoming-events.component';


// WHEN ADDING BG, ALSO ADD TO INDEX.HTML FOR PRELOADING
export const routes: Routes = [
  { path: '', component: StatsOverviewComponent, data: { bg: "assets/img/swing_feet.jpg", next: '/upcoming' } },
  { path: 'upcoming', component: StatsUpcomingEventsComponent, data: { bg: "assets/img/swingout.jpg", previous: '/' } },
];
