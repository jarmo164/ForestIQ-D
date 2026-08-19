import {Pipe, PipeTransform} from '@angular/core';

@Pipe({
  name: 'linkifyMessage'
})
export class MessageLinkifyPipe implements PipeTransform {

  transform(value: string, args?: any): any {
    if (!value) {
      return value;
    }

    const matches = value.match('\\d{11}');
    if (!matches) {
      return value;
    }

    let linkifiedValue = value;
    matches.forEach(idCode => {
      const rex = new RegExp(idCode, 'g');
      linkifiedValue = linkifiedValue.replace(rex, '<a href="/owners/' + idCode + '">' + idCode + '</a>');
    });
    return linkifiedValue;
  }
}
