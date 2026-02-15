import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { BehaviorSubject, Observable, Subject } from 'rxjs';
import { environment } from '../../environment';
import { pmo} from '../models/pmo';
import { SessionExpiredService } from './session-expired-service';

@Injectable({
  providedIn: 'root'
})
export class PMOService {
  private readonly url=environment.apiUrl;
  // public $refreshToken = new Subject<boolean>; 

  constructor(private http:HttpClient,
              // private sessionExpiredService: SessionExpiredService
  ) {
    // this.$refreshToken.subscribe((res:any) => {
    //   this.sessionExpiredService.getRefreshToken();
    // })
   }

   getProjects():Observable<any>{
    return this.http.get(this.url+'pmo/get-projects/')
  }
  createProjectAssignment(pmo:any){ 
  return this.http.post(this.url+'pmo/add-project/', pmo);
  }

  getProjectsById(projectCode:string):Observable<any>{
    return this.http.get(this.url+'pmo/get-project-by-code/'+projectCode+'/');
  }
  updatePMO(projectCode:string,pmo:any){
      return this.http.put(this.url+'pmo/edit-project/'+projectCode+'/',pmo);
    }
  getProjectTeam(projectCode:string):Observable<any>{
    return this.http.get(this.url+'pmo/display-project-team?project_code='+projectCode)
  }
  addProjectTeam(projectTeam:any){ 
    return this.http.post(this.url+'pmo/add-project-team/', projectTeam);
    }
  updateProjectTeam(projectTeam:any,projectCode:string){
    return this.http.put(this.url+'pmo/edit-project-team/',projectTeam);
  }
  deleteProjectTeam(projectCode: string): Observable<any> {
      return this.http.delete(this.url + 'pmo/delete-project-team/'+projectCode+'/');
    }

  addPhase(payload:any){ 
    return this.http.post(this.url+'pmo/phase-allocation-create-bulk', payload);
    // return this.http.post(this.url+'pmo/phase-allocation/', payload);
  }

  getPhases() {
    return this.http.get(this.url+'pmo/phase-allocation')
  }

  getPhasesByProject(projectCode:any) {
    return this.http.get(this.url+'pmo/pmo/phase-allocation/by-project/?project_code='+projectCode)
  }

  updatePhase(payload:any){ 
    return this.http.put(this.url+'pmo/phase-allocation/update-bulk/', payload);
    // return this.http.put(this.url+'pmo/phase-allocation/update/', payload);
  }

  createAndUpdatePhase(payload:any){ 
    return this.http.post(this.url+'pmo/phase-allocation/update/', payload);
  }

  deletePhase(phaseId: any): Observable<any> {
    return this.http.delete(this.url + 'pmo/phase-allocation/delete/'+phaseId+'/');
  }

  getPMOReport(payload:any){ 
    return this.http.post(this.url+'pmo/pmo-report/', payload);
  }

  getDateRangeAllocation(payload:any){ 
    return this.http.get(this.url+'pmo/api/employee-allocation-timesheet/?employee_code='+payload.employee_code+'&start_date='+payload.start_date+'&end_date='+payload.end_date);
  }

  allocationPercentage(payload:any){
    return this.http.post(this.url+'pmo/assign-allocation/', payload);
  }

  //get all projects of an emp having allocation %
  getEmpProjectDetails(emp_code:string):Observable<any>{
    return this.http.get(this.url+'pmo/api/employee/'+emp_code+'/projects/');
  }

  //add or update allocation %
  assignAllocationPercent(emp_code:string, payload:any):Observable<any>{
    return this.http.post<any[]>(this.url+'pmo/api/employee/'+emp_code+'/projects/', payload)
  }
}
