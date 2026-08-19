import {UserMinimal} from '../user/user-minimal';

export interface OwnerMinimal {
  id: string,
  name: string,
  status: string,
  statusSetAt: number,
  assignee: UserMinimal,
  phone: string,
}
