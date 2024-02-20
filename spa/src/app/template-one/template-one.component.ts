import { animate, state, style, transition, trigger } from '@angular/animations';
import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-template-one',
  standalone: true,
  imports: [],
  templateUrl: './template-one.component.html',
  styleUrl: './template-one.component.scss',
  animations: [
    trigger('contentSlide', [
      transition(':enter', style({ bottom: '-14rem' })),
      transition('* => true', [style({ bottom: '-14rem' }), animate('1200ms ease-in-out', style({ bottom: 0 }))]),
      state('false', style({ bottom: '-14rem' })),
      state('true', style({ bottom: 0 })),
    ])
  ],
})
export class TemplateOneComponent {
  @Input()
  isLoaded: boolean = false;
}
