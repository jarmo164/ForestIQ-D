import {ForestSection} from "./forest-section";

export interface ContractualCadastre {
  id: string,
  name: string,
  address: string,
  registrationPartNumber: string,
  forestSections: ForestSection[]
}
