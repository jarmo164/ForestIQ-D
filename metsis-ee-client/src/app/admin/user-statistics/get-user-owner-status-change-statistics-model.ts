import {UserMinimal} from '../../user/user-minimal';

export class GetUserOwnerStatusChangeStatisticsModel {
  public users: UserMinimal[];
  public fromStatuses: any[];
  public toStatuses: any[];
  public granularity: string = 'HOUR';
  public period: Date[] = [this.todayMidnight(), new Date()];

  constructor() {
  }

  private todayMidnight(): Date {
    let d = new Date();
    d.setHours(0,0,0,0);
    return d;
  }

  public getSince(): Date {
    return this.period.length >= 1 ? this.period[0] : null;
  }

  public getUpTo(): Date {
    return this.period.length >= 2 ? this.period[1] : null;
  }

  getFromStatuses() {
    return (this.fromStatuses || []).map(this.extractId);
  }

  getToStatuses() {
    return (this.toStatuses || []).map(this.extractId);
  }

  getUsers() {
    return (this.users || []).map(this.extractId);
  }

  private extractId(data) {
    return data.id;
  }
}
