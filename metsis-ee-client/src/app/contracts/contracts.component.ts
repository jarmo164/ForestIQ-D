import {Component, OnInit} from '@angular/core';
import {LoadableData} from '../loadable-data';
import {ContractData} from './models/contract-data';
import {ContractService} from './contract.service';
import {ContractualCadastre} from './models/contractual-cadastre';
import {ForestSection} from './models/forest-section';
import {SellerParty} from './models/seller-party';
import {CompleterData, CompleterItem, CompleterService} from 'ng2-completer';
import {BuyerParty} from './models/buyer-party';
import {ContractPartyProxy} from './models/contract-party-proxy';
import {Ng2IzitoastService} from 'ng2-izitoast';
import {HistoricalContractInfo} from './models/historical-contract-info';
import {ConfirmationDialogService} from '../confirmation-dialog/confirmation-dialog.service';
import {HistoricalContractsSearchFilter} from './models/historical-contracts-search-filter';
import {ContractParty} from './models/contract-party';

@Component({
  selector: 'app-contracts',
  templateUrl: './contracts.component.html',
  styleUrls: ['./contracts.component.scss']
})
export class ContractsComponent implements OnInit {

  contractData: LoadableData<ContractData> = new LoadableData<ContractData>();
  historicalContracts: LoadableData<HistoricalContractInfo[]> = new LoadableData<HistoricalContractInfo[]>();
  cadastreCompleter: CompleterData;
  ownerCompleter: CompleterData;
  historicalContractsSearchFilter: HistoricalContractsSearchFilter = new HistoricalContractsSearchFilter();
  bigLoaderVisible = false;

  constructor(
    private contractService: ContractService,
    private completerService: CompleterService,
    private iziToast: Ng2IzitoastService,
    private confirmationDialogService: ConfirmationDialogService) {
    this.cadastreCompleter = completerService.remote('api/services/contracts/autocompleters/cadastre/');
    this.ownerCompleter = completerService.remote('api/services/contracts/autocompleters/owner/');
  }

  ngOnInit() {
    this.loadContractDataModel(null);
  }

  loadContractDataModel(baseContractId?: string) {
    this.contractData.start();
    this.contractService.getPreparationData(baseContractId).subscribe(
      data => {
        this.contractData.dataReceived(data);
        this.contractData.data.contractDetails.dateOfEnforcement = new Date(this.contractData.data.contractDetails.dateOfEnforcement);
        this.contractData.data.contractDetails.finalDate = new Date(this.contractData.data.contractDetails.finalDate);
        this.listHistoricalContracts(0);
      },
      err => {
        this.contractData.errorReceived(err);
      }
    );
  }

  removeSection(sections: ForestSection[], index: number) {
    sections.splice(index, 1);
  }

  addSection(cadastre: ContractualCadastre) {
    cadastre.forestSections.push({
      sectionNumber: cadastre.forestSections.length + 1,
      typeOfWork: 'LR',
      amountToBeCut: 0.0,
      area: 0.0,
      notificationId: null
    });
  }

  removeCadastre(cadastres: ContractualCadastre[], index: number) {
    cadastres.splice(index, 1);
  }

  addCadastre() {
    this.contractData.data.contractDetails.cadastres.push({
      id: null,
      name: null,
      address: null,
      forestSections: [],
      registrationPartNumber: null,
    });
  }

  noProxy(party: ContractParty) {
    party.proxy = null;
  }

  yesProxy(party: ContractParty) {
    party.proxy = {
      name: null, code: null, contactInformation: {
        email: null, phoneNo: null, address: null
      }
    };
  }

  addSeller() {
    this.contractData.data.sellers.push(
      {
        bankAccountNumber: null,
        moneyObtainedFromTheDeal: null,
        code: null,
        name: null,
        vat: null,
        contactInformation: {
          email: null,
          phoneNo: null,
          address: null
        }
      });
  }

  removeSeller(sellers: SellerParty[], index: number) {
    sellers.splice(index, 1);
  }

  onCadastreSelect(selected: CompleterItem, cadastre: ContractualCadastre) {
    if (selected) {
      const selectedCadastre: string = selected.originalObject;
      this.bigLoaderVisible = true;
      this.contractService.getCadastreDetails(selectedCadastre).subscribe(data => {
        this.bigLoaderVisible = false;
        cadastre.name = data.name;
        cadastre.forestSections = data.forestSections;
        cadastre.address = data.address;
        cadastre.registrationPartNumber = data.registrationPartNumber;
      }, err => {
        this.bigLoaderVisible = false;
        cadastre.name = null;
        cadastre.forestSections = null;
        cadastre.address = null;
        cadastre.registrationPartNumber = null;
        const loadableData = new LoadableData();
        loadableData.errorReceived(err);
        this.iziToast.error({position: 'bottomLeft', message: loadableData.error});
      });
    }
  }

  onBuyerSelect(selected: CompleterItem, buyer: BuyerParty) {
    if (selected) {
      this.bigLoaderVisible = true;
      const selectedOwner: string = selected.originalObject;
      this.contractService.getOwnerDetails(selectedOwner).subscribe(data => {
        this.bigLoaderVisible = false;
        buyer.name = data.name;
        buyer.code = data.code;
        buyer.contactInformation = {
          email: data.contactInformation.email,
          phoneNo: data.contactInformation.phoneNo,
          address: data.contactInformation.address
        };
      }, err => {
        this.bigLoaderVisible = false;
        buyer.name = null;
        buyer.code = null;
        buyer.contactInformation = {
          email: null,
          phoneNo: null,
          address: null
        };
        buyer.proxy = null;
        const loadableData = new LoadableData();
        loadableData.errorReceived(err);
        this.iziToast.error({position: 'center', message: loadableData.error});
      });
    }
  }

  onSellerSelect(selected: CompleterItem, seller: SellerParty) {
    if (selected) {
      this.bigLoaderVisible = true;
      const selectedOwner: string = selected.originalObject;
      this.contractService.getOwnerDetails(selectedOwner).subscribe(data => {
        this.bigLoaderVisible = false;
        seller.name = data.name;
        seller.code = data.code;
        seller.contactInformation = {
          email: data.contactInformation.email,
          phoneNo: data.contactInformation.phoneNo,
          address: data.contactInformation.address
        };
      }, err => {
        this.bigLoaderVisible = false;
        seller.name = null;
        seller.code = null;
        seller.contactInformation = {
          email: null,
          phoneNo: null,
          address: null
        };
        const loadableData = new LoadableData();
        loadableData.errorReceived(err);
        this.iziToast.error({position: 'center', message: loadableData.error});
      });
    }
  }

  onProxySelect(selected: CompleterItem, proxy: ContractPartyProxy) {
    if (selected) {
      const selectedOwner: string = selected.originalObject;
      this.bigLoaderVisible = true;
      this.contractService.getOwnerDetails(selectedOwner).subscribe(data => {
        this.bigLoaderVisible = false;
        proxy.name = data.name;
        proxy.code = data.code;
      }, err => {
        this.bigLoaderVisible = false;
        proxy.name = null;
        proxy.code = null;
        const loadableData = new LoadableData();
        loadableData.errorReceived(err);
        this.iziToast.error({position: 'center', message: loadableData.error});
      });
    }
  }

  createContract(c: ContractData) {
    this.bigLoaderVisible = true;
    this.contractService.createContract(c).subscribe(data => {
      this.bigLoaderVisible = false;
      window.location.assign(data.path + '/' + data.baseId);
      this.listHistoricalContracts(0);
    }, err => {
      this.bigLoaderVisible = false;
      this.contractData.errorReceived(err);
      this.iziToast.error({position: 'center', message: this.contractData.error});
    });
  }

  listHistoricalContracts(offset: number) {
    this.historicalContractsSearchFilter.offset = offset;
    this.historicalContracts.start();
    this.contractService.listHistoricalContracts(this.historicalContractsSearchFilter).subscribe(
      data => {
        this.historicalContracts.dataReceived(data);
      }, err => {
        this.historicalContracts.errorReceived(err);
      }
    );
  }

  deleteContract(id: string) {
    this.confirmationDialogService.confirm('Are you sure?', 'Do you really want to delete the selected contract?')
      .then((confirmed) => {
        if (confirmed) {
          this.bigLoaderVisible = true;
          this.contractService.deleteContract(id).subscribe(
            () => {
              this.bigLoaderVisible = false;
              this.listHistoricalContracts(0);
              this.iziToast.success({position: 'center', message: 'Contract deleted.'});
            }, err => {
              this.bigLoaderVisible = false;
              this.historicalContracts.errorReceived(err);
            }
          );
        }
      });
  }
}
