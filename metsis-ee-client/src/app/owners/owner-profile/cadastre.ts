import {CadastreMinimal} from './cadastre-minimal';
import {OwnerMinimal} from '../owner-minimal';
import {CadastreSubPart} from "./cadastre-sub-part";

export interface Cadastre extends CadastreMinimal {
  municipality: string,
  county: string,
  address: string,
  regNr: string,
  postal: string,
  owners: OwnerMinimal[],
  labels: string[]
  cadastreSubParts: CadastreSubPart[],
  mkDate: number
}
