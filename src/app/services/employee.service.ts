import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';
import { environment } from '../../environment';

@Injectable({
  providedIn: 'root'
})
export class EmployeeService {
private readonly url=environment.apiUrl; 
private token = localStorage.getItem('access_token'); 
  constructor(private http:HttpClient) { }

   getTimesheets(employee_code:string):Observable<any>{
    return this.http.get(this.url+'employee/display-timesheet/'+employee_code+'/');
    // return this.http.get(this.url+'employee/display-timesheet');
  }

  saveTimesheet(timesheet:any){ 
  return this.http.post(this.url+'employee/timesheet-add/', timesheet);
  }

  updateTimesheet(timesheet:any){
      return this.http.put(this.url+'employee/timesheet-edit/',timesheet);
    }

    getTimesheetByEmployeeCode(obj:any):Observable<any>{
      return this.http.post(this.url+'employee/timesheets/employee_month_year/',obj);
    }

    getProjectDetailsByEmployeeCode(employee_code:string):Observable<any>{
      return this.http.get(this.url+'employee/display-employee-projects/'+employee_code);
    }

    getProjectHours(employee_code:any):Observable<any>{
      return this.http.post(this.url+'employee/get-project-hours/',employee_code);
    }

    getCountriesList():Observable<any>{
      return this.http.get(this.url+'employee/get_countries_list/')
    }
}
