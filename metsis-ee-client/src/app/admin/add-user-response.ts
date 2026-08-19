import {MaintainableUser} from './maintain-users/maintainable-user';

export interface AddUserResponse {
  user: MaintainableUser
  password: string
}
