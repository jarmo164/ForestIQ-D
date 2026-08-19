export class ChangeOwnerStatusModel {
  newStatus: string;
  comment: string;

  constructor() {}

  reset() {
    this.newStatus = null;
    this.comment = null;
  }
}
