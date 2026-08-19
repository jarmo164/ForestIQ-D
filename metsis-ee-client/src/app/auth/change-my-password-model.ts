export class ChangeMyPasswordModel {
  constructor(public oldPassword: string, public newPassword: string, public newPasswordAgain: string) {
  }

  reset() {
    this.oldPassword = null;
    this.newPassword = null;
    this.newPasswordAgain = null;
  }

}
