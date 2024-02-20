import { Routes } from '@angular/router';
import { StatsOverviewComponent } from './stats-overview/stats-overview.component';

export const routes: Routes = [
  { path: '', component: StatsOverviewComponent, data: { bg: "assets/img/swing_feet.jpg" } },
  { path: 'test', component: StatsOverviewComponent, data: { bg: "assets/img/swingout.jpg" } },
];
