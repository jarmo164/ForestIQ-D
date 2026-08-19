import {BuyerParty} from './buyer-party';
import {SellerParty} from './seller-party';
import {ContractDetails} from './contract-details';

export interface ContractData {
  contractNumber: string;
  buyer: BuyerParty;
  sellers: SellerParty[];
  contractDetails: ContractDetails;
  templateNumber: number;
}
