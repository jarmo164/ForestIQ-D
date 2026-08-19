export class Worksearchcriteria {
  public counties: string[];
  public municipalities: string[];
  public ownerTypes: string[];
  public minArea: number;
  public maxArea: number;
  public minTotalForrestArea: number;
  public maxTotalForrestArea: number;
  public minForrestArea: number;
  public maxForrestArea: number;
  public minArableArea: number;
  public maxArableArea: number;
  public conservationAreas: string = null;
  public suspendedFor: string[];
  public maxResults = 1000;
  public onlyWithPhoneNumbers: boolean;
  public onlyWithoutPhoneNumbers: boolean;
  public onlyWithoutForestPlans: boolean;
  public onlyWithNoStatus: boolean;
  public assignees: string[];
  public status: string;
  public hasNotificationsSince: Date;
  public hasForrestPlanSince: Date;
  public statusUpdatedSince: Date;
  public statusUpdatedTo: Date;
}
