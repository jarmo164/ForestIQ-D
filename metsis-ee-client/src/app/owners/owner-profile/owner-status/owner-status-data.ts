import {UserMinimal} from '../../../user/user-minimal';
import {OwnerStatus} from "../../owner-status-bubble/owner-status";

export interface OwnerStatusData {
  possibleAssignees: UserMinimal[],
  possibleOwnerStatuses: string[],
  status: OwnerStatus,
  assignee: UserMinimal
}
