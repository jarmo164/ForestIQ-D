import {Component, Input, OnInit} from '@angular/core';
import {LoadableData} from '../../../../loadable-data';
import {CadastreLabelsModel} from './cadastre-labels-model';
import {OwnersService} from '../../../owners.service';
import {Ng2IzitoastService} from 'ng2-izitoast';

@Component({
  selector: 'app-cadastre-labels',
  templateUrl: './cadastre-labels.component.html',
  styleUrls: ['./cadastre-labels.component.scss']
})
export class CadastreLabelsComponent implements OnInit {

  @Input('cadastre') cadastreId: string;

  cadastreLabels: LoadableData<CadastreLabelsModel> = new LoadableData<CadastreLabelsModel>();
  newLabel: string;

  constructor(private ownersService: OwnersService, private iziToast: Ng2IzitoastService) { }

  ngOnInit() {
    this.loadLabels();
  }

  private loadLabels() {
    this.cadastreLabels.start();
    this.ownersService.getCadastreLabels(this.cadastreId).subscribe(
      data => {
        this.cadastreLabels.dataReceived(data);
        this.newLabel = null;
      },
      err => {
        this.cadastreLabels.errorReceived(err);
      }
    );
  }

  addLabel() {
    this.cadastreLabels.start();
    this.ownersService.addCadastreLabel(this.cadastreId, this.newLabel).subscribe(
      () => {
        this.loadLabels();
        this.iziToast.success({position: 'topRight', message: 'Label added'});
      },
      err => {
        this.loadLabels();
        let loadableData = new LoadableData();
        loadableData.errorReceived(err);
        this.iziToast.error({position: 'topRight', message: loadableData.error});
      }
    );
  }

  removeLabel(label: string) {
    this.cadastreLabels.start();
    this.ownersService.removeCadastreLabel(this.cadastreId, label).subscribe(
      () => {
        this.loadLabels();
        this.iziToast.success({position: 'topRight', message: 'Label removed'});
      },
      err => {
        this.loadLabels();
        let loadableData = new LoadableData();
        loadableData.errorReceived(err);
        this.iziToast.error({position: 'topRight', message: loadableData.error});
      }
    );
  }
}
