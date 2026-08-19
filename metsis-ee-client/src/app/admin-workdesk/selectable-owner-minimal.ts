import {OwnerMinimal} from '../owners/owner-minimal';
import {UserMinimal} from '../user/user-minimal';

export class SelectableOwnerMinimal implements OwnerMinimal{
  public id: string;
  public name: string;
  public selected: boolean = true;
  public status: string;
  public statusSetAt: number;
  public assignee: UserMinimal;
  public phone: string;

  constructor(owner: OwnerMinimal) {
    this.id = owner.id;
    this.name = owner.name;
    this.status = owner.status;
    this.statusSetAt = owner.statusSetAt;
    this.assignee = owner.assignee;
    this.phone = owner.phone
  }
}
