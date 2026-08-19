import {Pipe, PipeTransform} from '@angular/core';

@Pipe({name: 'translateCode'})
export class TranslateCode implements PipeTransform {

  public static translations = {
    'ASSIGNED' : 'Assigned',
    'WAITS_FOR_EVALUATION' : 'Waits evaluation',
    'IN_PROGRESS': 'In progress',
    'EVALUATED' : 'Evaluated',
    'DEAL' : 'Deal has been reached',
    'NO_DEAL_LARGE_OWNER' : 'Big landowner',
    'NO_DEAL_OWNER_NOT_INTERESTED' : 'Owner currently not interested',
    'NO_DEAL_OWNER_UNREACHABLE' : 'Does not answer phone',
    'NO_DEAL_WRONG_OWNER_PHONE_NUMBER' : 'Wrong phone number',
    'NO_DEAL_NO_LAND' : 'Does not have land',
    'NO_DEAL_OWNER_DOES_NOT_WANT_TO_TALK' : 'Do not disturb ',
    'NO_DEAL_OWNER_DEAD' : 'Dead',
    'NO_DEAL_TOO_EXPENSIVE' : 'Price too high',
    'NO_DEAL_OWNER_WONT_SELL' : 'Owner wont sell',
    'NO_DEAL_OWNER_IS_BUYER' : 'Owner is buyer'
  };

  transform(input: string): string {
    return TranslateCode.translations[input] || input;
  }
}
