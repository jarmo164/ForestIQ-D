import {CadastreMinimal} from './cadastre-minimal';
import {OwnerMinimal} from '../owner-minimal';
import {CoordinatePoint} from "./coordinate-point";

export interface CadastreSubPart {
  municipality: string,
  county: string,
  address: string,
  regNr: string,
  type: string,
  postal: string,
  owners: OwnerMinimal[]

  subPartCode: number,
  treeTypeCode: string,
  area: number,
  polygon: CoordinatePoint[]
}
