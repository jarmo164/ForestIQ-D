import {UserMinimal} from '../user/user-minimal';

export class AdminWorkdeskPreparationData {
  public counties: any[] = [];
  public municipalities: any[] = [];
  public ownerTypes: any[] = [];
  public callers: UserMinimal[] = [];
  public statuses: any[] = [];
  public assignees: any[] = [];

  constructor(data: IAdminWorkdeskPreparationData) {
    data.counties.forEach(elem => {
      this.counties.push({id: elem, itemName: elem});
    });
    data.municipalities.forEach(elem => {
      this.municipalities.push({id: elem, itemName: elem});
    });
    data.ownerTypes.forEach(elem => {
      this.ownerTypes.push({id: elem, itemName: elem});
    });
    data.statuses.forEach(elem => {
      this.statuses.push({id: elem, itemName: elem});
    });
    data.callers.forEach(elem => {
      this.assignees.push({id: elem.id, itemName: elem.name});
    });
    this.callers = data.callers;
  }
}

export interface IAdminWorkdeskPreparationData {
  counties: string[],
  municipalities: string[],
  callers: UserMinimal[],
  ownerTypes: string[],
  statuses: string[];
}
