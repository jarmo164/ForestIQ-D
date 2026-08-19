import {CoordinatePoint} from "../coordinate-point";

export interface MkData {
  cadastreSubParts: CadasreSubPart[]
}

export interface CadasreSubPart {
  subPartCode: number,
  area: number,
  treeTypeCode: string,
  polygon: CoordinatePoint[]
}
