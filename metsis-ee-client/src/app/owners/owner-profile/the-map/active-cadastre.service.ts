import {Injectable} from '@angular/core';

@Injectable()
export class ActiveCadastreService {

  constructor() {
  }

  private zoomToEstoniaFn: Function;
  private zoomToActiveFn: Function;
  private activateCadastrePaneFn: Function;
  private activateCadastreOnMapFn: Function;
  private unsetActicveCadastreFromMapFn: Function;
  private unsetActicveCadastreFromPaneFn: Function;

  setZoomFns(zoomToEstonia: Function, zoomToActive: Function) {
    this.zoomToEstoniaFn = zoomToEstonia;
    this.zoomToActiveFn = zoomToActive;
  }

  setActivateCadastrePaneFn(activateCadastrePaneFn: Function) {
    this.activateCadastrePaneFn = activateCadastrePaneFn;
  }

  setActivateCadastreOnMapFn(activateCadastreOnMapFn: Function) {
    this.activateCadastreOnMapFn = activateCadastreOnMapFn;
  }

  setUnsetActicveCadastreFromMapFn(unsetActicveCadastreFromMapFn: Function){
    this.unsetActicveCadastreFromMapFn = unsetActicveCadastreFromMapFn;
  }

  setUnsetActicveCadastreFromPaneFn(unsetActicveCadastreFromPaneFn: Function){
    this.unsetActicveCadastreFromPaneFn = unsetActicveCadastreFromPaneFn;
  }

  zoomToEstonia() {
    if (this.zoomToEstoniaFn) {
      this.zoomToEstoniaFn();
    }
  }

  zoomToActive() {
    if (this.zoomToActiveFn) {
      this.zoomToActiveFn();
    }
  }

  activateCadastre(cadastreNo: string) {
    if (this.activateCadastrePaneFn) {
      this.activateCadastrePaneFn(cadastreNo);
    }

    if (this.activateCadastreOnMapFn) {
      this.activateCadastreOnMapFn(cadastreNo);
    }
  }

  deactivate() {
    if (this.unsetActicveCadastreFromMapFn) {
      this.unsetActicveCadastreFromMapFn();
    }
    if (this.unsetActicveCadastreFromPaneFn) {
      this.unsetActicveCadastreFromPaneFn();
    }
  }
}
