import {BrowserModule} from '@angular/platform-browser';
import {NgModule} from '@angular/core';

import {AppRoutingModule} from './app-routing.module';

import {AppComponent} from './app.component';
import {HomeComponent} from './home/home.component';
import {AdminComponent} from './admin/admin.component';
import {MeComponent} from './me/me.component';
import {MaintainUsersComponent} from './admin/maintain-users/maintain-users.component';
import {HTTP_INTERCEPTORS, HttpClientModule} from '@angular/common/http';
import {AdminService} from './admin/admin.service';
import {ApiErrorHandler} from './api-error-handler';
import {BrowserAnimationsModule} from '@angular/platform-browser/animations';
import {Ng2IziToastModule} from 'ng2-izitoast';
import {FormsModule, ReactiveFormsModule} from '@angular/forms';
import {AuthService} from './auth/auth-service';
import {NgbModule} from '@ng-bootstrap/ng-bootstrap';
import {ConfirmationDialogComponent} from './confirmation-dialog/confirmation-dialog.component';
import {ConfirmationDialogService} from './confirmation-dialog/confirmation-dialog.service';
import {JwtModule} from '@auth0/angular-jwt';
import {AdminGuard} from './admin/admin.guard';
import {TokenInterceptor} from './auth/token.interceptor';
import {MeGuard} from './me/me.guard';
import {OwnersComponent} from './owners/owners.component';
import {OwnersGuard} from './owners/owners.guard';
import {OwnersService} from './owners/owners.service';
import {AgmCoreModule, GoogleMapsAPIWrapper} from '@agm/core';
import {CommonModule} from '@angular/common';
import {OwnerProfileComponent} from './owners/owner-profile/owner-profile.component';
import {environment} from '../environments/environment';
import {TheMapComponent} from './owners/owner-profile/the-map/the-map.component';
import {AdminWorkdeskComponent} from './admin-workdesk/admin-workdesk.component';
import {AngularMultiSelectModule} from 'angular2-multiselect-dropdown';
import {AdminWorkdeskService} from './admin-workdesk/admin-workdesk.service';
import {OrderBy} from './utilities/orderby.pipe';
import {TranslateCode} from './utilities/translate.pipe';
import {OwnerLogComponent} from './owners/owner-profile/owner-log/owner-log.component';
import {CadastreProfileComponent} from './owners/owner-profile/cadastre-profile/cadastre-profile.component';
import {ActiveCadastreService} from './owners/owner-profile/the-map/active-cadastre.service';
import {CadastreEvalutationComponent} from './owners/owner-profile/cadastre-profile/cadastre-evalutation/cadastre-evalutation.component';
import {EvaluatorWorkdeskComponent} from './evaluator-workdesk/evaluator-workdesk.component';
import {EvaluationGuard} from './evaluator-workdesk/evaluation.guard';
import {CallerWordeskComponent} from './caller-wordesk/caller-wordesk.component';
import {OwnerStatusBubbleComponent} from './owners/owner-status-bubble/owner-status-bubble.component';
import {OwnerStatusComponent} from './owners/owner-profile/owner-status/owner-status.component';
import {WorkSearchComponent} from './admin-workdesk/work-search/work-search.component';
import {ReassignWorkComponent} from './admin-workdesk/reassign-work/reassign-work.component';
import {CadastreLabelsComponent} from './owners/owner-profile/cadastre-profile/cadastre-labels/cadastre-labels.component';
import {AssignedOwnersGuard} from './owners/assigned-owners.guard';
import {UserStatisticsComponent} from './admin/user-statistics/user-statistics.component';
import {UserStatisticsService} from './admin/user-statistics/user-statistics.service';
import {OWL_DATE_TIME_LOCALE, OwlDateTimeModule, OwlNativeDateTimeModule} from 'ng-pick-datetime';
import {AreasComponent} from './owners/owner-profile/cadastre-profile/areas/areas.component';
import {
  CadastreNotificationsComponent
} from './owners/owner-profile/cadastre-profile/cadastre-notifications/cadastre-notifications.component';
import {RegistryFeaturesComponent} from './owners/owner-profile/cadastre-profile/registry-features/registry-features.component';
import {ContractsComponent} from './contracts/contracts.component';
import {ContractService} from './contracts/contract.service';
import {Ng2CompleterModule} from 'ng2-completer';
import {MaintainOwnerStatusesComponent} from './admin/maintain-owner-statuses/maintain-owner-statuses.component';
import {PersonsDumpComponent} from './persons-dump/persons-dump.component';
import {PersonsDumpService} from './persons-dump/persons-dump.service';
import {PersonsDumpGuard} from './persons-dump/persons-dump.guard';
import {RemindersComponent} from './reminders/reminders.component';
import {RemindersService} from './reminders/reminders.service';
import { MessagesComponent } from './messages/messages.component';
import { IncomingMessagesComponent } from './messages/incoming-messages/incoming-messages.component';
import { OutgoingMessagesComponent } from './messages/outgoing-messages/outgoing-messages.component';
import {MessageLinkifyPipe} from './messages/message-linkify.pipe';
import { RemindersDashboardComponent } from './reminders-dashboard/reminders-dashboard.component';

@NgModule({
  declarations: [
    AppComponent,
    HomeComponent,
    AdminComponent,
    MeComponent,
    MaintainUsersComponent,
    ConfirmationDialogComponent,
    OwnersComponent,
    OwnerProfileComponent,
    TheMapComponent,
    AdminWorkdeskComponent,
    OrderBy,
    TranslateCode,
    OwnerLogComponent,
    CadastreProfileComponent,
    CadastreEvalutationComponent,
    EvaluatorWorkdeskComponent,
    CallerWordeskComponent,
    OwnerStatusBubbleComponent,
    OwnerStatusComponent,
    WorkSearchComponent,
    ReassignWorkComponent,
    CadastreLabelsComponent,
    UserStatisticsComponent,
    AreasComponent,
    CadastreNotificationsComponent,
    RegistryFeaturesComponent,
    ContractsComponent,
    MaintainOwnerStatusesComponent,
    PersonsDumpComponent,
    RemindersComponent,
    MessagesComponent,
    IncomingMessagesComponent,
    OutgoingMessagesComponent,
    MessageLinkifyPipe,
    RemindersDashboardComponent
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    CommonModule,
    FormsModule,
    Ng2CompleterModule,
    AppRoutingModule,
    HttpClientModule,
    AngularMultiSelectModule,
    Ng2IziToastModule,
    OwlDateTimeModule,
    OwlNativeDateTimeModule,
    NgbModule,
    JwtModule.forRoot({
      config: {
        tokenGetter: () => {
          return localStorage.getItem('auth_token');
        }
      }
    }),
    AgmCoreModule.forRoot({
      apiKey: environment.google_maps_key,
      libraries: ['geometry']
    }),
    ReactiveFormsModule
  ],
  providers: [
    {
      provide: HTTP_INTERCEPTORS,
      useClass: TokenInterceptor,
      multi: true
    },
    AdminService,
    AuthService,
    OwnersService,
    AdminWorkdeskService,
    ContractService,
    AdminGuard,
    MeGuard,
    OwnersGuard,
    EvaluationGuard,
    AssignedOwnersGuard,
    PersonsDumpGuard,
    ApiErrorHandler,
    ConfirmationDialogService,
    ActiveCadastreService,
    UserStatisticsService,
    PersonsDumpService,
    RemindersService,
    GoogleMapsAPIWrapper,
    OrderBy,
    TranslateCode,
    {provide: OWL_DATE_TIME_LOCALE, useValue: 'en-GB'}
  ],
  entryComponents: [ConfirmationDialogComponent],
  bootstrap: [AppComponent]
})
export class AppModule {
}
