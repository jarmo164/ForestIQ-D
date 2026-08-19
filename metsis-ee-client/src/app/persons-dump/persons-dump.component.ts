import {Component, OnInit} from '@angular/core';
import {PersonsDumpService} from './persons-dump.service';
import {PersonsDumpCriteria} from './persons-dump-criteria';
import {PersonsDumpEntry} from './persons-dump-entry';
import {LoadableData} from '../loadable-data';
import {Subscription} from 'rxjs';
import {FormBuilder, FormGroup} from '@angular/forms';
import {NewPhonebookEntry} from './new-phonebook-entry';
import {Ng2IzitoastService} from 'ng2-izitoast';

@Component({
  selector: 'app-persons-dump',
  templateUrl: './persons-dump.component.html',
  styleUrls: ['./persons-dump.component.scss']
})
export class PersonsDumpComponent implements OnInit {

  personsDumpCriteria: PersonsDumpCriteria = new PersonsDumpCriteria();
  personsDumpSearchResult: LoadableData<PersonsDumpEntry[]> = new LoadableData<PersonsDumpEntry[]>();
  private searchObservableSubscription: Subscription;
  addEntryLoading = false;

  addPhonebookEntryForm: FormGroup;

  constructor(
    private personsDumpService: PersonsDumpService,
    private iziToast: Ng2IzitoastService,
    formBuilder: FormBuilder) {
    this.addPhonebookEntryForm = formBuilder.group(new NewPhonebookEntry());
  }

  ngOnInit() {
    this.search();
  }

  onAddPersonSubmit(entry: NewPhonebookEntry) {
    this.addEntryLoading = true;
    this.personsDumpService.addEntry(entry).subscribe(
      () => {
        this.search();
        this.addPhonebookEntryForm.reset();
        this.addEntryLoading = false;
        this.iziToast.success({position: 'bottomRight', message: 'New phonebook entry added.'});
      },
      error => {
        const x = new LoadableData();
        x.errorReceived(error);
        this.iziToast.error({position: 'bottomRight', message: 'Error happened when adding a new phonebook entry ' + x.error});
        this.addEntryLoading = false;
      }
    );
  }

  search() {
    this.personsDumpSearchResult.start();
    try {
      this.searchObservableSubscription.unsubscribe();
    } catch (e) {
    }
    this.searchObservableSubscription = this.personsDumpService.search(this.personsDumpCriteria).subscribe(
      data => {
        this.personsDumpSearchResult.dataReceived(data);
      },
      err => {
        this.personsDumpSearchResult.errorReceived(err);
      }
    );
  }

  deleteEntry(id: number) {
    if (confirm('Do you really want to delete this entry?')) {
      this.personsDumpService.deleteEntry(id).subscribe(
        () => {
          this.search();
        }, error => {
          const x = new LoadableData();
          x.errorReceived(error);
          this.iziToast.error({position: 'bottomRight', message: 'Error deleting entry ' + x.error});
        }
      );
    }
  }
}
