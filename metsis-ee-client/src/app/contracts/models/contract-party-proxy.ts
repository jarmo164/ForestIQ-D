import {ContactInformation} from './contact-information';

export interface ContractPartyProxy {
  proxyRepresentationBase?: string;
  name: string;
  code: string;
  contactInformation: ContactInformation;
}
