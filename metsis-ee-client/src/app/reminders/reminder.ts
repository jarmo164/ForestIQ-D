import {OwnerMinimal} from '../owners/owner-minimal';

export interface Reminder {
  id: number;
  creator: string;
  owner: OwnerMinimal;
  text: string;
  cadastre: string;
  propertyName: string;
  dueTime: Date;
  createdTime: Date;
}
