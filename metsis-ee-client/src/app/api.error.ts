import {ApiErrorCode} from './api.error.code';

export class ApiError {

  constructor(public code: ApiErrorCode, public message: string) {
  }

}
