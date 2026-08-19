import {Component, Input, OnInit} from '@angular/core';
import {OwnersService} from "../../../owners.service";
import {LoadableData} from "../../../../loadable-data";
import {Areas} from "./areas";

@Component({
  selector: 'app-areas',
  templateUrl: './areas.component.html',
  styleUrls: ['./areas.component.scss']
})
export class AreasComponent implements OnInit {

  @Input('cadastre') cadastreId: string;
  areas: LoadableData<Areas> = new LoadableData<Areas>();

  constructor(private ownersService : OwnersService) { }

  ngOnInit() {
    this.areas.start();
    this.ownersService.getCadastreAreas(this.cadastreId, true).subscribe(
      data => {
        this.areas.dataReceived(data);
      }, err => {
        this.areas.errorReceived(err);
      }
    )
  }
}
