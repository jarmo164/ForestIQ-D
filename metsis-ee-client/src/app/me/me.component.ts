import {Component, OnInit} from '@angular/core';
import {AuthService} from '../auth/auth-service';
import {ChangeMyPasswordModel} from '../auth/change-my-password-model';
import {LoadableData} from '../loadable-data';

@Component({
  selector: 'app-me',
  templateUrl: './me.component.html',
  styleUrls: ['./me.component.scss']
})
export class MeComponent implements OnInit {

  pwChangeModel: ChangeMyPasswordModel = new ChangeMyPasswordModel(null, null, null);
  pwChange: LoadableData<any> = new LoadableData<any>();

  constructor(private authService: AuthService) {
  }

  ngOnInit() {
  }

  changePassword(pwChangeModel: ChangeMyPasswordModel) {
    this.pwChange.start();
    this.authService.changeMyPassword(pwChangeModel).subscribe(
      () => {
        this.pwChange.dataReceived('OK');
        pwChangeModel.reset();
      },
      (err) => {
        this.pwChange.errorReceived(err);
        pwChangeModel.reset();
      });
  }

}
