import {Component, Input, OnInit} from '@angular/core';
import {OwnersService} from '../../../owners.service';
import {LoadableData} from '../../../../loadable-data';
import {CadastreEvaluation} from './cadastre-evaluation';
import {Ng2IzitoastService} from 'ng2-izitoast';

@Component({
  selector: 'app-cadastre-evalutation',
  templateUrl: './cadastre-evalutation.component.html',
  styleUrls: ['./cadastre-evalutation.component.scss']
})
export class CadastreEvalutationComponent implements OnInit {

  @Input() cadastre: string;

  latestEvaluation : LoadableData<CadastreEvaluation> = new LoadableData<CadastreEvaluation>();
  evaluationSubmit: LoadableData<any> = new LoadableData<any>();

  constructor(private ownersService: OwnersService, private iziToast: Ng2IzitoastService) { }

  ngOnInit() {
    if (!this.cadastre) {
      this.latestEvaluation.errorReceived("Can not find evaluation without cadastre number");
      return;
    }
    this.loadEvaluation();
  }

  private loadEvaluation() {
    this.latestEvaluation.start();
    this.ownersService.getLatestCadastreEvaluation(this.cadastre).subscribe(
      data => {
        this.latestEvaluation.dataReceived(data);
        this.evaluationSubmit.reset();
      },
      error => {
        this.latestEvaluation.errorReceived(error);
      }
    );
  }

  submitEvaluation() {
    let data = this.latestEvaluation.data;
    this.evaluationSubmit.start();
    this.ownersService.saveEvaluation(this.cadastre, data).subscribe(
      () => {
        this.iziToast.success({position: 'topRight', message: 'Evaluation saved'});
        this.loadEvaluation();
      },
      error => {
        this.evaluationSubmit.errorReceived(error);
      }
    );
  }

}
