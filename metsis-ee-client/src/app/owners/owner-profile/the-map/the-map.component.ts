import {AfterViewInit, Component, Input, NgZone} from '@angular/core';
import {GoogleMapsAPIWrapper} from '@agm/core';
import {Owner} from '../owner';
import {GoogleMap, Marker, Polygon} from '@agm/core/services/google-maps-types';
import {CoordinatePoint} from '../coordinate-point';
import {MarkerIcons} from './marker-icons';
import {ActiveCadastreService} from './active-cadastre.service';
import {OwnersService} from "../../owners.service";
import {LoadableData} from "../../../loadable-data";
import {Ng2IzitoastService} from "ng2-izitoast";
import {MkData} from "../cadastre-profile/mk-data";

declare let google: any;
declare let MapLabel: any;

@Component({
  selector: 'app-the-map',
  templateUrl: './the-map.component.html',
  styleUrls: ['./the-map.component.scss']
})
export class TheMapComponent implements AfterViewInit {

  private markers: Map<string, MarkerWithIcon> = new Map<string, MarkerWithIcon>();
  private polygons: Map<string, Polygon> = new Map<string, Polygon>();
  private mkPolygons: Polygon[] = [];
  private mapLabels = [];
  private activeCadastre: ActiveCadastre;

  @Input() set owner(owner: Owner) {
    this.removeMapLayers();
    this.mapApiWrapper.getNativeMap().then((map) => {
      if (owner) {
        this.addMapLayers(map, owner);
      }
    });
  }

  constructor(
    private mapApiWrapper: GoogleMapsAPIWrapper, private ngZone: NgZone, private activeCadastreService: ActiveCadastreService,
    private ownersService: OwnersService, private iziToast: Ng2IzitoastService
  ) {
    this.activeCadastreService.setZoomFns(this.zoomToEstonia.bind(this), this.zoomToActiveCadastre.bind(this));
    this.activeCadastreService.setActivateCadastreOnMapFn(this.setActiveCadastre.bind(this));
    this.activeCadastreService.setUnsetActicveCadastreFromMapFn(this.unsetActiveCadastre.bind(this));
  }

  private getBounds(paths) {
    let bounds = new google.maps.LatLngBounds();
    let path;
    for (let i = 0; i < paths.getLength(); i++) {
      path = paths.getAt(i);
      for (let ii = 0; ii < path.getLength(); ii++) {
        bounds.extend(path.getAt(ii));
      }
    }
    return bounds;
  }

  ngAfterViewInit() {
    this.zoomToEstonia();
  }

  private zoomToEstonia() {
    this.mapApiWrapper.getNativeMap().then((map) => {
      this.initMapExtras();
      new google.maps.Geocoder().geocode({'address': 'Estonia'}, function (results, status) {
        if (status === google.maps.GeocoderStatus.OK) {
          map.setCenter(results[0].geometry.location);
          map.setZoom(8);
        }
      });
    });
  }

  private zoomToActiveCadastre() {
    this.mapApiWrapper.getNativeMap().then((map) => {
      if (this.activeCadastre && this.activeCadastre.polygon) {
        map.fitBounds(this.getBounds(this.activeCadastre.polygon.getPaths()));
      } else if (this.activeCadastre && this.activeCadastre.marker) {
        map.setCenter(this.activeCadastre.center);
        map.setZoom(15);
      }
    });
  }

  private removeMapLayers() {
    this.unsetActiveCadastre();
    this.markers.forEach((marker: MarkerWithIcon, cadastreNo: string) => {
      marker.marker.setMap(null);
    });
    this.markers.clear();
    this.polygons.forEach((polygon: Polygon, cadastreNo: string) => polygon.setMap(null));
    this.polygons.clear();
  }

  setActiveCadastre(cadastreNo: string) {
    this.unsetActiveCadastre();
    if (cadastreNo) {
      this.ownersService.getMkData(cadastreNo, true).subscribe((mkData) => {
          let marker = this.markers.get(cadastreNo);
          if (!marker) {
            return;
          }
          this.activeCadastre = new ActiveCadastre(cadastreNo, marker.marker, this.polygons.get(cadastreNo), marker.icon, mkData, marker.position);
          if (this.activeCadastre) {
            this.activeCadastre.marker.setIcon(MarkerIcons.LAND_ACTIVE);
            this.zoomToActiveCadastre();
            this.mapApiWrapper.getNativeMap().then((map) => {
              this.mkPolygons.forEach(polygon => {
                polygon.setMap(null);
              });
              this.mkPolygons = [];
              (this.activeCadastre.mkData.cadastreSubParts || []).forEach(coords => {
                let polygon: Polygon = new google.maps.Polygon({
                  paths: coords.polygon,
                  strokeColor: '#ff6d00',
                  strokeOpacity: 0.8,
                  strokeWeight: 2,
                  fillOpacity: 0.2,
                  map: map
                });
                this.mkPolygons.push(polygon);
                let centroid = this.getApproximateCenter(polygon);
                let mapLabel = new MapLabel({
                  text: (coords.subPartCode + ':' + coords.treeTypeCode),
                  position: centroid,
                  map: map,
                  fontSize: 10,
                  align: 'left'
                });
                this.mapLabels.push(mapLabel);
                mapLabel.set('position', centroid);
              });
            });
          }
        },
        err => {
          let loadableData = new LoadableData();
          loadableData.errorReceived(err);
          this.iziToast.error({position: 'topRight', message: loadableData.error});
        });
    }
  }

  private unsetActiveCadastre() {
    if (this.activeCadastre) {
      this.activeCadastre.marker.setIcon(this.activeCadastre.icon);
    }
    this.mapApiWrapper.getNativeMap().then((map) => {
      this.mkPolygons.forEach(polygon => {
        polygon.setMap(null);
      });
      this.mkPolygons = [];
      this.mapLabels.forEach(label => {
        label.setMap(null);
      });
      this.mapLabels = [];
    });
    this.activeCadastre = null;
  }

  private addMapLayers(map: GoogleMap, owner: Owner) {
    owner.cadastres.forEach(cadastre => {
      this.addMarker(cadastre.id, cadastre.centroid, this.resolveMarkerIcon(cadastre.type), map);
      if (cadastre.polygon) {
        this.addPolygon(cadastre.id, cadastre.polygon, map);
      }
    });
  }

  private resolveMarkerIcon(landType: string): string {
    if (!landType) {
      return MarkerIcons.LAND;
    }
    if (landType.startsWith("Maatulundus")) {
      return MarkerIcons.FOREST;
    }
    if (landType.startsWith("Elamu")) {
      return MarkerIcons.LIVING;
    }
    if (landType.startsWith("Tootmis")) {
      return MarkerIcons.PRODUCTION;
    }
    if (landType.startsWith("Transpor")) {
      return MarkerIcons.TRANSPORT;
    }
    if (landType.startsWith("Kaitse")) {
      return MarkerIcons.CONSERVATION;
    }
    if (landType.startsWith("Äri")) {
      return MarkerIcons.BUSINESS;
    }
    return MarkerIcons.LAND;
  }

  private addMarker(cadastreNo: string, coordinates: CoordinatePoint, icon: string, map: GoogleMap) {
    let marker: Marker = new google.maps.Marker({
      position: coordinates,
      map: map,
      icon: icon
    });
    let self = this;
    marker.addListener('click', function () {
      self.ngZone.run(() => {
        self.activeCadastreService.activateCadastre(cadastreNo);
      });
    });
    this.markers.set(cadastreNo, new MarkerWithIcon(marker, icon, coordinates));
  }

  private addPolygon(cadastreNo: string, coordinates: CoordinatePoint[], map: GoogleMap) {
    try {
      let polygon: Polygon = new google.maps.Polygon({
        paths: coordinates,
        strokeColor: '#0800ff',
        strokeOpacity: 0.8,
        strokeWeight: 2,
        fillOpacity: 0,
        map: map
      });
      this.polygons.set(cadastreNo, polygon);
    } catch (ex) {
      console.log(ex);
    }
  }

  private getApproximateCenter(polygon) {
    let boundsHeight = 0,
      boundsWidth = 0,
      centerPoint,
      heightIncr = 0,
      maxSearchLoops,
      maxSearchSteps = 10,
      n = 1,
      northWest,
      polygonBounds = polygon.getBoundingBox(),
      testPos,
      widthIncr = 0;


    // Get polygon Centroid
    centerPoint = polygonBounds.getCenter();

    if (google.maps.geometry.poly.containsLocation(centerPoint, polygon)) {
      // Nothing to do Centroid is in polygon use it as is
      return centerPoint;
    } else {
      maxSearchLoops = maxSearchSteps / 2;


      // Calculate NorthWest point so we can work out height of polygon NW->SE
      northWest = new google.maps.LatLng(
        polygonBounds.getNorthEast().lat(),
        polygonBounds.getSouthWest().lng()
      );


      // Work out how tall and wide the bounds are and what our search
      // increment will be
      boundsHeight = google.maps.geometry.spherical.computeDistanceBetween(
        northWest,
        polygonBounds.getSouthWest()
      );
      heightIncr = boundsHeight / maxSearchSteps;


      boundsWidth = google.maps.geometry.spherical.computeDistanceBetween(
        northWest, polygonBounds.getNorthEast()
      );
      widthIncr = boundsWidth / maxSearchSteps;


      // Expand out from Centroid and find a point within polygon at
      // 0, 90, 180, 270 degrees
      for (; n <= maxSearchSteps; n++) {
        // Test point North of Centroid
        testPos = google.maps.geometry.spherical.computeOffset(
          centerPoint,
          (heightIncr * n),
          0
        );
        if (this.containsLocation(testPos, polygon)) {
          break;
        }


        // Test point East of Centroid
        testPos = google.maps.geometry.spherical.computeOffset(
          centerPoint,
          (widthIncr * n),
          90
        );
        if (this.containsLocation(testPos, polygon)) {
          break;
        }


        // Test point South of Centroid
        testPos = google.maps.geometry.spherical.computeOffset(
          centerPoint,
          (heightIncr * n),
          180
        );
        if (this.containsLocation(testPos, polygon)) {
          break;
        }


        // Test point West of Centroid
        testPos = google.maps.geometry.spherical.computeOffset(
          centerPoint,
          (widthIncr * n),
          270
        );
        if (this.containsLocation(testPos, polygon)) {
          break;
        }
      }


      return (testPos);
    }
  }

  private containsLocation(testPos, polygon) {
    try {
      return google.maps.geometry.poly.containsLocation(testPos, polygon);
    } catch (e) {
      return false;
    }
  }

  private initMapExtras() {

    google.maps.Polygon.prototype.getBoundingBox = function () {
      let bounds = new google.maps.LatLngBounds();


      this.getPath().forEach(function (element, index) {
        bounds.extend(element)
      });


      return (bounds);
    };

    /**
     * @license
     *
     * Copyright 2011 Google Inc.
     *
     * Licensed under the Apache License, Version 2.0 (the "License");
     * you may not use this file except in compliance with the License.
     * You may obtain a copy of the License at
     *
     *     http://www.apache.org/licenses/LICENSE-2.0
     *
     * Unless required by applicable law or agreed to in writing, software
     * distributed under the License is distributed on an "AS IS" BASIS,
     * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
     * See the License for the specific language governing permissions and
     * limitations under the License.
     */

    /**
     * @fileoverview Map Label.
     *
     * @author Luke Mahe (lukem@google.com),
     *         Chris Broadfoot (cbro@google.com)
     */

    /**
     * Creates a new Map Label
     * @constructor
     * @extends google.maps.OverlayView
     * @param {Object.<string, *>=} opt_options Optional properties to set.
     */
    function MapLabel(opt_options) {
      this.set('fontFamily', 'sans-serif');
      this.set('fontSize', 12);
      this.set('fontColor', '#000000');
      this.set('strokeWeight', 4);
      this.set('strokeColor', '#ffffff');
      this.set('align', 'center');

      this.set('zIndex', 1e3);

      this.setValues(opt_options);
    }

    MapLabel.prototype = new google.maps.OverlayView;

    window['MapLabel'] = MapLabel;


    /** @inheritDoc */
    MapLabel.prototype.changed = function (prop) {
      switch (prop) {
        case 'fontFamily':
        case 'fontSize':
        case 'fontColor':
        case 'strokeWeight':
        case 'strokeColor':
        case 'align':
        case 'text':
          return this.drawCanvas_();
        case 'maxZoom':
        case 'minZoom':
        case 'position':
          return this.draw();
      }
    };

    /**
     * Draws the label to the canvas 2d context.
     * @private
     */
    MapLabel.prototype.drawCanvas_ = function () {
      let canvas = this.canvas_;
      if (!canvas) return;

      let style = canvas.style;
      style.zIndex = /** @type number */(this.get('zIndex'));

      let ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.strokeStyle = this.get('strokeColor');
      ctx.fillStyle = this.get('fontColor');
      ctx.font = this.get('fontSize') + 'px ' + this.get('fontFamily');

      let strokeWeight = Number(this.get('strokeWeight'));

      let text = this.get('text');
      if (text) {
        if (strokeWeight) {
          ctx.lineWidth = strokeWeight;
          ctx.strokeText(text, strokeWeight, strokeWeight);
        }

        ctx.fillText(text, strokeWeight, strokeWeight);

        let textMeasure = ctx.measureText(text);
        let textWidth = textMeasure.width + strokeWeight;
        style.marginLeft = this.getMarginLeft_(textWidth) + 'px';
        // Bring actual text top in line with desired latitude.
        // Cheaper than calculating height of text.
        style.marginTop = '-0.4em';
      }
    };

    /**
     * @inheritDoc
     */
    MapLabel.prototype.onAdd = function () {
      let canvas = this.canvas_ = document.createElement('canvas');
      let style = canvas.style;
      style.position = 'absolute';

      let ctx = canvas.getContext('2d');
      ctx.lineJoin = 'round';
      ctx.textBaseline = 'top';

      this.drawCanvas_();

      let panes = this.getPanes();
      if (panes) {
        panes.mapPane.appendChild(canvas);
      }
    };
    MapLabel.prototype['onAdd'] = MapLabel.prototype.onAdd;

    /**
     * Gets the appropriate margin-left for the canvas.
     * @private
     * @param {number} textWidth  the width of the text, in pixels.
     * @return {number} the margin-left, in pixels.
     */
    MapLabel.prototype.getMarginLeft_ = function (textWidth) {
      switch (this.get('align')) {
        case 'left':
          return 0;
        case 'right':
          return -textWidth;
      }
      return textWidth / -2;
    };

    /**
     * @inheritDoc
     */
    MapLabel.prototype.draw = function () {
      let projection = this.getProjection();

      if (!projection) {
        // The map projection is not ready yet so do nothing
        return;
      }

      if (!this.canvas_) {
        // onAdd has not been called yet.
        return;
      }

      let latLng = /** @type {google.maps.LatLng} */ (this.get('position'));
      if (!latLng) {
        return;
      }
      let pos = projection.fromLatLngToDivPixel(latLng);

      let style = this.canvas_.style;

      style['top'] = pos.y + 'px';
      style['left'] = pos.x + 'px';

      style['visibility'] = this.getVisible_();
    };
    MapLabel.prototype['draw'] = MapLabel.prototype.draw;

    /**
     * Get the visibility of the label.
     * @private
     * @return {string} blank string if visible, 'hidden' if invisible.
     */
    MapLabel.prototype.getVisible_ = function () {
      let minZoom = /** @type number */(this.get('minZoom'));
      let maxZoom = /** @type number */(this.get('maxZoom'));

      if (minZoom === undefined && maxZoom === undefined) {
        return '';
      }

      let map = this.getMap();
      if (!map) {
        return '';
      }

      let mapZoom = map.getZoom();
      if (mapZoom < minZoom || mapZoom > maxZoom) {
        return 'hidden';
      }
      return '';
    };

    /**
     * @inheritDoc
     */
    MapLabel.prototype.onRemove = function () {
      let canvas = this.canvas_;
      if (canvas && canvas.parentNode) {
        canvas.parentNode.removeChild(canvas);
      }
    };
    MapLabel.prototype['onRemove'] = MapLabel.prototype.onRemove;
  }
}

class ActiveCadastre {
  constructor(public cadastreNo: string, public marker: Marker, public polygon: Polygon, public icon: string, public mkData: MkData, public center: CoordinatePoint) {
  }
}

class MarkerWithIcon {
  constructor(public marker: Marker, public icon: string, public position: CoordinatePoint) {

  }
}
