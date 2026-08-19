export class MyWorkSearchCriteria {

  public id: string;
  public name: string;
  public phone: string;
  public email: string;
  public cadastre: string;
  public statuses: any[];
  public order: string;
  public direction: string;

  constructor() {
  }

  statusIds() : string[] {
    return this.statuses.map(status => status.id);
  }
}
