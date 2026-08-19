export interface ForestRegistryFeature {
  id: number,
  sourceLayer: string,
  sourceId: string,
  cadastreId: string,
  subpartCode: number,
  title: string,
  workCode: string,
  decision: string,
  area: number,
  volume: number,
  eventDate: number,
  attributes: string,
  geometry: string
}
