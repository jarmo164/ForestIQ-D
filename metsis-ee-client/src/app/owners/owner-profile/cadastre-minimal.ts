import {CoordinatePoint} from './coordinate-point';

export interface CadastreMinimal {
  id: string,
  name: string,
  centroid: CoordinatePoint,
  polygon: CoordinatePoint[],
  area: number,
  marked: boolean,
  type: string
}
