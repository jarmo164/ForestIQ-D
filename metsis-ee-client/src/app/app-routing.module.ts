import {NgModule} from '@angular/core';
import {RouterModule, Routes} from '@angular/router';
import {HomeComponent} from './home/home.component';
import {AdminComponent} from './admin/admin.component';
import {MeComponent} from './me/me.component';
import {AdminGuard} from './admin/admin.guard';
import {MeGuard} from './me/me.guard';
import {OwnersComponent} from './owners/owners.component';
import {OwnersGuard} from './owners/owners.guard';
import {OwnerProfileComponent} from './owners/owner-profile/owner-profile.component';
import {AdminWorkdeskComponent} from './admin-workdesk/admin-workdesk.component';
import {EvaluatorWorkdeskComponent} from './evaluator-workdesk/evaluator-workdesk.component';
import {EvaluationGuard} from './evaluator-workdesk/evaluation.guard';
import {CallerWordeskComponent} from './caller-wordesk/caller-wordesk.component';
import {AssignedOwnersGuard} from './owners/assigned-owners.guard';
import {ContractsComponent} from './contracts/contracts.component';
import {PersonsDumpComponent} from './persons-dump/persons-dump.component';
import {PersonsDumpGuard} from './persons-dump/persons-dump.guard';
import {RemindersComponent} from './reminders/reminders.component';
import {MessagesComponent} from './messages/messages.component';
import {RemindersDashboardComponent} from './reminders-dashboard/reminders-dashboard.component';

const routes: Routes = [
  {
    path: '',
    redirectTo: 'home',
    pathMatch: 'full'
  },
  {
    path: 'home',
    component: HomeComponent
  },
  {
    path: 'owners',
    component: OwnersComponent,
    canActivate: [OwnersGuard]
  },
  {
    path: 'owners/:id',
    component: OwnerProfileComponent,
    canActivate: [AssignedOwnersGuard]
  },
  {
    path: 'admin',
    component: AdminComponent,
    canActivate: [AdminGuard]
  },
  {
    path: 'workdesk/admin',
    component: AdminWorkdeskComponent,
    canActivate: [AdminGuard]
  },
  {
    path: 'reminders-dashboard',
    component: RemindersDashboardComponent,
    canActivate: [AdminGuard]
  },
  {
    path: 'workdesk/evaluator',
    component: EvaluatorWorkdeskComponent,
    canActivate: [EvaluationGuard]
  },
  {
    path: 'phones',
    component: PersonsDumpComponent,
    canActivate: [PersonsDumpGuard]
  },
  {
    path: 'workdesk/caller',
    component: CallerWordeskComponent,
    canActivate: [AssignedOwnersGuard]
  },
  {
    path: 'contracts',
    component: ContractsComponent,
    canActivate: [AdminGuard]
  },
  {
    path: 'reminders',
    component: RemindersComponent,
    canActivate: [OwnersGuard]
  },
  {
    path: 'messages',
    component: MessagesComponent,
    canActivate: [MeGuard]
  },
  {
    path: 'me',
    component: MeComponent,
    canActivate: [MeGuard]
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule {
}
