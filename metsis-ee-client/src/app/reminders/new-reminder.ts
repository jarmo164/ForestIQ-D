import {Reminder} from './reminder';
import {OwnerMinimal} from '../owners/owner-minimal';
import {UserMinimal} from '../user/user-minimal';

export class NewReminder implements Reminder {
  owner: OwnerMinimal = new NewRemindersOwner();
  text: string;
  cadastre: string;
  propertyName: string;
  dueTime: any;
  creator: string;
  id: number;
  createdTime: Date;
}

export class NewRemindersOwner implements OwnerMinimal {
  assignee: UserMinimal;
  id: string;
  name: string;
  status: string;
  statusSetAt: number;
  phone: string;

}
