import { inject, Injectable } from '@angular/core';
import { environment } from '../../environment';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})

export class AssetManagementService {

  constructor() { }
  http = inject(HttpClient)

  private readonly url=environment.apiUrl;

  getAllCategories(type:string):Observable<any>{
      return this.http.get(this.url+'master_data/grouped-asset-categories/?asset_type='+type);
  }

  getAllCompanies():Observable<any>{
      return this.http.get(this.url+'master_data/companies/locations/');
  }

  viewPdfFile(fileUrl: string): Observable<Blob> {
    const encoded = encodeURIComponent(fileUrl || '');
    //done for hardware file view, having issue with this link
    // return this.http.get(this.url + 'inventory/download-file/?file_path=' + encoded, { responseType: 'blob' });

    //done for software file view, no issues and using for both hardware and software files view
    return this.http.get(this.url + '/software/software-assignment/view_file/?file_url=' + encoded, { responseType: 'blob' });
  }

  //get all hardwares
  getAllHardwares():Observable<any>{
      return this.http.get(this.url+'inventory/hardware-assignments/');
  }
  
  //add hardware
  addHardware(data:any){ 
     return this.http.post(this.url+'inventory/hardware-assignments/create/', data);
  }

  //get hardware by id
  getHardwareById(id: string): Observable<any> {
    return this.http.get(this.url +'inventory/hardware-assignments/'+id+'/');
  }

  //update hardware
  updateHardware(id:string, data:any){
    return this.http.put(this.url + 'inventory/hardware-assignments/'+id+'/update/', data)
  }

  //get all softwares
  getAllSoftwares():Observable<any>{
      return this.http.get(this.url+'software/software-assignments/');
  }

  //add softwares
  addSoftware(data:any){ 
     return this.http.post(this.url+'software/software-assignment/create/', data);
   }

  //get software by id
  getSoftwareById(id: string): Observable<any> {
    return this.http.get(this.url + 'software/software-assignment/'+id+'/');
  }

  //update software
  updateSoftware(id:string, data:any){
    return this.http.put(this.url + 'software/software-assignment/'+id+'/update/', data)
  }
}
