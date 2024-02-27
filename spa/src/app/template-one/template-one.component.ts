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
      transition(':enter', style({ marginTop: '100lvh' })),
      transition('* => true', [style({ marginTop: '100lvh' }), animate('1000ms ease-out', style({ marginTop: 'calc(100svh - 15rem)' }))]),
      state('false', style({ marginTop: '100lvh' })),
      state('true', style({ marginTop: 'calc(100svh - 15rem)' })),
    ])
  ],
})
export class TemplateOneComponent {
  @Input()
  isLoaded: boolean = false;
}
