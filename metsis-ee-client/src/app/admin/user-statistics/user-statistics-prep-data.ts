import {UserMinimal} from '../../user/user-minimal';

export interface IUserStatisticsPrepData {
  users: UserMinimal[],
  ownerStatuses: string[]
}

export class UserStatisticsPrepData {
  public users: any[] = [];
  public ownerStatuses: any[] = [{id: null, itemName: 'Undefinded'}];

  constructor(data: IUserStatisticsPrepData) {
    data.users.forEach(elem => {
      this.users.push({id: elem.id, itemName: elem.name});
    });
    data.ownerStatuses.forEach(elem => {
      this.ownerStatuses.push({id: elem, itemName: elem});
    });
  }
}
