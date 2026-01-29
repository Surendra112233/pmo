import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from 'src/environment';

@Injectable({
  providedIn: 'root'
})
export class TravelService {
  private readonly url=environment.apiUrl; 
  private token = localStorage.getItem('access_token'); 
  constructor(private http:HttpClient) { }

  // Request Raise By Employee
  raiseRequest(body:any): Observable<any>{
    return this.http.post(this.url+'travel_requestapi/travel-request/',body)
  }

  getAllRequests():Observable<any>{
    return this.http.get(this.url+'travel_requestapi/travel-request/all/')
  }

  getTravelDetailsByRequestId(id:any):Observable<any>{
    return this.http.get(this.url+'travel_requestapi/travel-request/'+id+'/')
  }

  updateTravelRequest(id:any,body:any):Observable<any>{
    return this.http.patch(this.url+'travel_requestapi/travel-request/'+id+'/edit/',body)
  }

  approveOrRejectRequest(id:any,body:any):Observable<any>{
    return this.http.post(this.url+'travel_requestapi/travel-request/'+id+'/action/',body)
  }

}
