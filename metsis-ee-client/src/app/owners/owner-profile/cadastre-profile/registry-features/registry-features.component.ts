import {Component, Input, OnInit} from '@angular/core';
import {LoadableData} from '../../../../loadable-data';
import {OwnersService} from '../../../owners.service';
import {ForestRegistryFeature} from './forest-registry-feature';

@Component({
  selector: 'app-registry-features',
  templateUrl: './registry-features.component.html',
  styleUrls: ['./registry-features.component.scss']
})
export class RegistryFeaturesComponent implements OnInit {

  @Input() cadastre: string;

  features: LoadableData<ForestRegistryFeature[]> = new LoadableData<ForestRegistryFeature[]>();

  constructor(private ownersService: OwnersService) { }

  ngOnInit() {
    this.features.start();
    this.ownersService.getForestRegistryFeatures(this.cadastre).subscribe(
      data => {
        this.features.dataReceived(data);
      },
      err => {
        this.features.errorReceived(err);
      }
    );
  }

  layerLabel(feature: ForestRegistryFeature): string {
    return (feature.sourceLayer || '').replace('metsaregister:', '');
  }

  hasDetails(feature: ForestRegistryFeature): boolean {
    return !!(feature.workCode || feature.decision || feature.area || feature.volume || feature.subpartCode);
  }
}
