import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'countryName',
  standalone: true
})
export class CountryNamePipe implements PipeTransform {

  transform(value: string, ...args: unknown[]): string {
    const [countryName] = value.split('_');
    return countryName;
  }

}
