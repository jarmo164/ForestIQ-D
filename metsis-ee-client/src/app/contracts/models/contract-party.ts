import {ContactInformation} from './contact-information';
import {ContractPartyProxy} from './contract-party-proxy';

export interface ContractParty {
  code: string;
  name: string;
  contactInformation: ContactInformation;
  proxy?: ContractPartyProxy;
}
