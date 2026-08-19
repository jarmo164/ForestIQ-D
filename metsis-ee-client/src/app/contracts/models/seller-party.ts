import {ContractParty} from './contract-party';

export interface SellerParty extends ContractParty {
  vat: string;
  bankAccountNumber: string;
  moneyObtainedFromTheDeal: number;
}
