import {ApiError} from './api.error';

export class LoadableData<T> {
  data: T = null;
  error: string = null;
  errorCode: string = null;
  loading: boolean = false;

  start() {
    this.data = null;
    this.error = null;
    this.errorCode = null;
    this.loading = true;
  }

  errorReceived(error: any) {
    if (error instanceof ApiError) {
      this.errorCode = error.code;
      this.error = error.message;
    } else {
      this.error = error == null ? null : error.toString();
    }
    this.loading = false;
  }

  dataReceived(data: T) {
    this.loading = false;
    this.data = data;
  }

  reset() {
    this.data = null;
    this.error = null;
    this.errorCode = null;
    this.loading = false;
  }

  any(): boolean {
    return !!this.data || !!this.error || this.loading;
  }
}
