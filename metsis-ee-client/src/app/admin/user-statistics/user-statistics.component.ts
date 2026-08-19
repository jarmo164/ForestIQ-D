import {Component, Input, OnDestroy, OnInit} from '@angular/core';
import {UserStatisticsService} from './user-statistics.service';
import {GetUserOwnerStatusChangeStatisticsModel} from './get-user-owner-status-change-statistics-model';
import {LoadableData} from '../../loadable-data';
import {UserOwnerStatusChangeStatistics} from './user-owner-status-change-statistics';
import {UserStatisticsPrepData} from './user-statistics-prep-data';
import {Chart} from 'chart.js';
import {Owner} from '../../owners/owner-profile/owner';

@Component({
  selector: 'app-user-statistics',
  templateUrl: './user-statistics.component.html',
  styleUrls: ['./user-statistics.component.scss']
})
export class UserStatisticsComponent implements OnInit, OnDestroy {

  prepData: LoadableData<UserStatisticsPrepData> = new LoadableData<UserStatisticsPrepData>();

  searchModel: GetUserOwnerStatusChangeStatisticsModel = new GetUserOwnerStatusChangeStatisticsModel();
  statisticsData: LoadableData<UserOwnerStatusChangeStatistics[]> = new LoadableData<UserOwnerStatusChangeStatistics[]>();

  chart: any;
  totals: any;

  @Input()
  simple: boolean;

  _autoRefreshOn = false;

  @Input() set autoRefreshOn(autoRefreshOn: boolean) {
    this._autoRefreshOn = autoRefreshOn;
    this.toggleAutoRefresh();
  }
  autoRefresher;

  constructor(private userStatisticsService: UserStatisticsService) {
  }

  ngOnInit() {
    this.prepData.start();
    this.userStatisticsService.getPrepData().subscribe(
      data => {
        this.prepData.dataReceived(data);
        if (this.simple) {
          this.searchModel.fromStatuses = data.ownerStatuses;
          this.searchModel.toStatuses = data.ownerStatuses;
          this.searchModel.granularity = 'HOUR';
          this.searchModel.users = data.users;
          const yesterdayMidnight = new Date();
          yesterdayMidnight.setDate(yesterdayMidnight.getDate() - 1);
          yesterdayMidnight.setHours(0, 0, 0, 0);
          this.searchModel.period = [yesterdayMidnight, new Date()];
          this.getStatistics();
        }
      }, err => {
        this.prepData.errorReceived(err);
      }
    );
  }

  ngOnDestroy(): void {
    if (this.autoRefresher) {
      clearInterval(this.autoRefresher);
    }
  }

  getStatistics() {
    this.statisticsData.start();
    if (this.chart) {
      this.chart.destroy();
    }
    this.userStatisticsService.getStatistics(this.searchModel).subscribe(data => {
      this.statisticsData.dataReceived(data);

      const dateLabels = data[0].statisticsFrame.map(frame => new Date(frame.since).toLocaleTimeString('en-GB', {
        year: 'numeric',
        month: 'numeric',
        day: 'numeric'
      }));

      this.chart = new Chart('canvas', {
        type: 'line',
        data: {
          labels: dateLabels,
          datasets: this.createChartJSData(data)
        },
        options: {
          maintainAspectRatio: false,
          legend: {
            display: true
          },
          scales: {
            xAxes: [{display: true}],
            yAxes: [{display: true}]
          }
        }
      });
      this.totals = data.map(user => {
        return {
          name: this.prepData.data.users.filter(u => u.id == user.userId)[0].itemName,
          total: user.statisticsFrame.map(fr => fr.count).reduce(function (a, b) {
            return a + b;
          }, 0)
        };
      });
    }, error => {
      this.statisticsData.errorReceived(error);
    });

  }


  private createChartJSData(data: UserOwnerStatusChangeStatistics[]): any {
    const colors = [
      '#3cba9f',
      '#000bba',
      '#6d00ba',
      '#ba0056',
      '#00abba',
      '#ba4c00',
      '#b8ba00',
      '#096eba',
      '#36ba00',
      '#ba9a9a',
      '#9b00ba',
      '#0d8c86',
      '#9cba96',
      '#ba0026',
      '#b0bab5',
      '#7cba00',
      '#ba7e00',
      '#0a0a0a'
    ];
    const result = [];
    for (let i = 0; i < data.length; i++) {
      if (data[i].statisticsFrame.find(fr => fr.count > 0)) {
        const color = colors[i < colors.length - 1 ? i : (i - (colors.length - i))];
        const series = data[i].statisticsFrame.map(fr => fr.count);
        const fullName = this.prepData.data.users.filter(u => u.id == data[i].userId)[0].itemName;
        result.push({
          label: fullName,
          data: series,
          borderColor: color,
          fill: false
        });
      }
    }
    return result;
  }

  toggleAutoRefresh() {
    if (this._autoRefreshOn) {
      if (this.autoRefresher) {
        clearInterval(this.autoRefresher);
      }
      const self = this;
      this.queryUntilNow();
      this.autoRefresher = setInterval(function () {
        console.log('Autorefresh poll activated...');
        self.queryUntilNow();
      }, 60000);
    } else {
      if (this.autoRefresher) {
        clearInterval(this.autoRefresher);
        this.autoRefresher = null;
      }
    }
  }

  private queryUntilNow() {
    this.searchModel.period[1] = new Date();
    this.getStatistics();
  }
}
