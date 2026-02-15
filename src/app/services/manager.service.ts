import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { environment } from 'src/environment';
import { BehaviorSubject, Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ManagerService {
private readonly url=environment.apiUrl; 
  constructor(private http:HttpClient) { }

getAllTimesheets(obj:any):Observable<any>{
    return this.http.post(this.url+'/manager/timesheet/approve/all/',obj);
  }

getTimesheetProjectCode(obj:any):Observable<any>{
    return this.http.post(this.url+'/manager/timesheet/approve/',obj);
  }

timesheetApproval(obj:any){
  return this.http.put(this.url+'/manager/timesheet/approve/reject/', obj);
}

getProjectSummaryReport(req:any):Observable<any>{
  return this.http.post<any[]>(this.url+'manager/project-summary/',req)
}
getProjectDetailReport(req:any):Observable<any>{
  return this.http.post<any[]>(this.url+'manager/project-detailed/',req)
}
getProjectSummaryPeriodWiseReport(req:any):Observable<any>{
  return this.http.post<any[]>(this.url+'manager/get_project_summary_periodwise/',req)
}
getProjectDetailedPeriodWiseReport(req:any):Observable<any>{
  return this.http.post<any[]>(this.url+'manager/get_project_detailed_periodwise/',req)
}
getProjectWiseEmpDetailsReport(req:any):Observable<any>{
  return this.http.get(this.url+'pmo/api/project/'+req+ '/employee-details/')
}
getEmployeeProjectDurationReport(project_code:string, days:string):Observable<any>{
  return this.http.get(this.url+'employee/get_project_duration_report/?project_code='+project_code+'&date_range='+days)
}
getEmployeeSummaryReport(req:any):Observable<any>{
  return this.http.post<any[]>(this.url+'manager/employee-summary/',req)
}
getEmployeeDetailReport(req:any):Observable<any>{
  return this.http.post<any[]>(this.url+'manager/employee-detailed/',req)
}

getAllEmployeeCumulativeReport(start_date:any, end_date:any):Observable<any>{
  return this.http.get(this.url+'employee/emp-utilization-report/?from_date='+start_date+'&to_date='+end_date)
}

getEmployeeCumulativeReport(emp_code:any, start_date:any, end_date:any):Observable<any>{
  return this.http.get(this.url+'employee/emp-utilization-report/?employee_code='+emp_code+'&from_date='+start_date+'&to_date='+end_date)
}

getEmployeeAvailabilityReport(days:any):Observable<any>{
  return this.http.get(this.url+'pmo/employee-availability/?availability_period='+days)
}

getPhasesByProjectCode(projectCode:any) {
  return this.http.post(this.url+'manager/get-projecthours-by-proejct/', projectCode)
}
      
}
