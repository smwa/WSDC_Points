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
      transition(':enter', style({ marginTop: '110vh' })),
      transition('* => true', [style({ marginTop: '110vh' }), animate('1000ms ease-out', style({ marginTop: '80vh' }))]),
      state('false', style({ marginTop: '110vh' })),
      state('true', style({ marginTop: '80vh' })),
    ])
  ],
})
export class TemplateOneComponent {
  @Input()
  isLoaded: boolean = false;
}
