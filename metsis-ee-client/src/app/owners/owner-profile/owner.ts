import {OwnerMinimal} from '../owner-minimal';
import {CadastreMinimal} from './cadastre-minimal';
import {UserMinimal} from '../../user/user-minimal';

export interface Owner extends OwnerMinimal {
  email: string,
  address: string,
  info: string,
  assignee: UserMinimal,
  type: string,
  cadastres: CadastreMinimal[],
  lastCadastreListRefresh: number
}
