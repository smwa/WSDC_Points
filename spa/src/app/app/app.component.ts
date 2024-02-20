import { Component } from '@angular/core';
import { ActivatedRoute, NavigationEnd, NavigationStart, Router, RouterOutlet } from '@angular/router';
import { Subscription, filter } from 'rxjs';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {
  swap_class = 'transitioning';
  background_image = '';
  transitioning_timeout = setTimeout(() => {}, 0);

  constructor(router: Router, route: ActivatedRoute) {

    router.events.subscribe((val) => {
      if (val instanceof NavigationEnd) {
        route.firstChild?.data.forEach((v) => {
          this.swap_class = 'transitioning';
          var new_background_image = v['bg'];

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
}
