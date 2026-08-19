import {Component, Input, OnInit} from '@angular/core';
import {OwnerStatus} from "./owner-status";

@Component({
  selector: 'app-owner-status-bubble',
  templateUrl: './owner-status-bubble.component.html',
  styleUrls: ['./owner-status-bubble.component.scss']
})
export class OwnerStatusBubbleComponent implements OnInit {

  @Input() status: OwnerStatus;

  constructor() { }

  ngOnInit() {
  }

}
