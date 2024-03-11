import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { TemplateOneComponent } from '../template-one/template-one.component';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { Dancer, Database, DatabaseFetcherService } from '../database-fetcher.service';

@Component({
  selector: 'app-dancer-page',
  standalone: true,
  imports: [
    CommonModule,
    TemplateOneComponent,
    RouterModule,
  ],
  templateUrl: './dancer-page.component.html',
  styleUrl: './dancer-page.component.scss'
})
export class DancerPageComponent implements OnInit {
  database: Database|undefined;
  is_loaded = false;
  dancer: undefined|Dancer = undefined;
  dancer_id: undefined|number = undefined;

  constructor(private databaseFetcher: DatabaseFetcherService, private route: ActivatedRoute) {
  }

  ngOnInit() {
    this.is_loaded = false;
    this.dancer = undefined;


    this.route.params.subscribe(
      params => {
        this.dancer_id = parseInt(params['id'], 10);
        this.dancer = this.database?.dancers.filter((_dancer) => _dancer.id == this.dancer_id)[0];
      }
    );


    this.databaseFetcher.database.subscribe((db) => {
      this.database = db;
      this.dancer = this.database?.dancers.filter((_dancer) => _dancer.id == this.dancer_id)[0];
      setTimeout(() => {
        this.is_loaded = true;
      }, 0)
    });
  }

  get_event_by_id(event_id: number) {
    return this.database?.events.filter((_event) => _event.id == event_id)[0];
  }

  format_placement_result(placement: string) {
    if (placement === '11') return '11th';
    if (placement === '12') return '12th';
    if (placement === '13') return '13th';
    if (placement.substring(-1) === '1') return `${placement}st`;
    if (placement.substring(-1) === '2') return `${placement}nd`;
    if (placement.substring(-1) === '3') return `${placement}rd`;
    if (parseInt(placement, 10) > 1) return `${placement}th`;
    return placement;
  }

  getPointsByDivision(): {role: string, division: string, points: number}[] {
    const byDivision: {role: string, division: string, points: number}[] = [];

    this.dancer?.placements.forEach((placement) => {
      const division = this.database?.divisions[placement.division];
      const role = this.database?.roles[placement.role];
      const points = placement.points;
      let added = false;
      byDivision.forEach((byDivisionItem) => {
        if (byDivisionItem.division === division && byDivisionItem.role === role) {
          byDivisionItem.points += points;
          added = true;
        }
      });
      if (!added) {
        byDivision.push({
          division: division || 'Unknown',
          role: role || 'Unknown',
          points: points,
        });
      }
    });

    return byDivision;
  }
}
