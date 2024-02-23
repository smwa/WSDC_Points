import { Component, OnDestroy, OnInit } from '@angular/core';
import { TemplateOneComponent } from '../template-one/template-one.component';

@Component({
  selector: 'app-about-us-page',
  standalone: true,
  imports: [
    TemplateOneComponent,
  ],
  templateUrl: './about-us-page.component.html',
  styleUrl: './about-us-page.component.scss'
})
export class AboutUsPageComponent implements OnInit, OnDestroy {
  is_loaded = false;

  ngOnInit(): void {
    setTimeout(() => {
      this.is_loaded = true
    }, 0);
  }

  ngOnDestroy(): void {
    this.is_loaded = false;
  }

}
