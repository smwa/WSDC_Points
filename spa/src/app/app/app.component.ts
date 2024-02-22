import { CommonModule, Location } from '@angular/common';
import { Component } from '@angular/core';
import { ActivatedRoute, NavigationEnd, Router, RouterModule, RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    RouterOutlet,
    RouterModule,
    CommonModule,
  ],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {
  swap_class = 'transitioning';
  next_link = undefined;
  prev_link = undefined;
  background_image = '';
  transitioning_timeout = setTimeout(() => {}, 0);

  constructor(router: Router, route: ActivatedRoute, private location: Location) {

    router.events.subscribe((val) => {
      if (val instanceof NavigationEnd) {
        route.firstChild?.data.forEach((v) => {
          this.swap_class = 'transitioning';
          var new_background_image = v['bg'];
          this.next_link = v['next'] || undefined;
          this.prev_link = v['previous'] || undefined;

          clearTimeout(this.transitioning_timeout);
          this.transitioning_timeout = setTimeout(() => {
            this.background_image = new_background_image;
            setTimeout(() => {
              this.swap_class = '';
            }, 1)
          }, 300);
        });
      }
    })

  }

  goback() {
    this.location.back();
  }
}
