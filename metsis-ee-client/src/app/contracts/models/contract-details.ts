import {ContractualCadastre} from './contractual-cadastre';

export interface ContractDetails {
  vatWithWords: string;
  vat: number;
  dateOfEnforcement: Date;
  finalDate: Date;
  price: number;
  writtenPrice: string;
  bankDaysToPayUp: number;
  bankDaysToPayUpCondition: boolean;
  cadastres: ContractualCadastre[];
  additionalTerms: string;
}
