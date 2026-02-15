import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';
import { environment } from '../../environment';
import { Tasks} from '../models/tasks';
import { Employee} from '../models/employee';

@Injectable({
  providedIn: 'root'
})
export class MasterDataService {

 private readonly url=environment.apiUrl; 
   private token = localStorage.getItem('access_token'); 
 
  //  private headers = new HttpHeaders({
  //    'Authorization': `Bearer ${this.token}`
  //  });
 
   constructor(private http:HttpClient) { }
 
  //  getTasks():Observable<any>{
  //   const headers=this.headers;
  //   return this.http.get(this.url+'master_data/display-task/',{ headers })
  // }
    getTasks():Observable<any>{
     return this.http.get(this.url+'master_data/display-task/');
   }
   getTasksById(task_code:number):Observable<any>{
    return this.http.get(this.url+'master_data/display-task-byid/'+task_code+'/');
  }
 
   addTask(task:any){ 
     return this.http.post(this.url+'master_data/add-task/', task);
   }

   updateTask(task_code:number,task:Tasks){
       return this.http.put(this.url+'master_data/edit-task/'+task_code+'/',task);
     }

     deleteTask(task_code: number): Observable<any> {
        return this.http.delete(this.url + 'master_data/delete-task/'+task_code+'/');
      }
  
   //Employee
   getEmployeeDetails():Observable<any>{
    return this.http.get(this.url+'master_data/display-employee/')
  }
   
  getActiveEmployeeDetails(flag:boolean):Observable<any>{
    return this.http.get(this.url+'master_data/display_name/?is_active='+flag);
  }

  getEmployeeById(employee_code:string):Observable<any>{
    return this.http.get(this.url+'master_data/display-employee-byid/'+employee_code+'/');
  }
  
  addEmployee(employee:any){
      return this.http.post(this.url+'master_data/add-employee/',employee);
    }

  updateEmployee(employee_code:string,employee:Employee){
      return this.http.put(this.url+'master_data/edit-employee/'+employee_code+'/',employee);
    }
  
    getProjectRoles():Observable<any>{
      return this.http.get(this.url+'master_data/display-projectroles/')
    }
    getProjectRolesById(id:number):Observable<any>{
      return this.http.get(this.url+'master_data/display-projectrole-byid/'+id+'/');
    }
    addProjectRoles(projectRoles:any){
        return this.http.post(this.url+'master_data/add-projectroles/',projectRoles);
      }

    updateProjectRoles(projectRoleId:number,projectRoles:any){
        return this.http.put(this.url+'master_data/edit-projectroles/'+projectRoleId+'/',projectRoles);
      }

    getPhasesWithDescription(project_code:string):Observable<any>{
      return this.http.get(this.url+'master_data/task-descriptions-by-phase-projectcode/?project_code='+project_code);
      // return this.http.get(this.url+'master_data/task-descriptions-by-phase/');
    }

    getEmployeeSummaryReport(req:any):Observable<any>{
      return this.http.post<any[]>(this.url+'master_data/get-employee-summary-report',req)
    }
    getEmployeeSummaryProjectWiseReport(req:any):Observable<any>{
      return this.http.post<any[]>(this.url+'master_data/get-employee-summary-report-detailed-byproject',req)
    }
    getEmployeeDetailReport(req:any):Observable<any>{
      return this.http.post<any[]>(this.url+'master_data/get-employee-summary-report-detailed',req)
    }
    getMissedEntriesReport(req:any):Observable<any>{
      return this.http.post<any[]>(this.url+'pmo/pmo-missed_timesheet/',req)
    }

    getDashboardResponse(year:any, employee_code:string):Observable<any>{
      return this.http.get(this.url+'master_data/employee-dashboard/'+year+'/'+employee_code+'/');
    }
    
    getManagerDashboardResponse(project_code:string):Observable<any>{
      return this.http.get(this.url+'master_data/manager-dashboard/'+project_code+'/');
    }

  //add asset category
  addAssetCategory(payload:any):Observable<any>{
    return this.http.post<any[]>(this.url+'master_data/add-asset_categories/', payload)
  }
  
  //update asset category
  updateAssetCategory(id:string, payload:any){
    return this.http.put(this.url+'master_data/asset_categories/'+id+'/', payload);
  }

  //get all asset categories
  getAllAssetCategories():Observable<any>{
      return this.http.get(this.url+'master_data/asset-categories/all/');
  }

  //delete asset category by id
  deleteAssetCategoryById(id:string):Observable<any>{
      return this.http.delete(this.url+'master_data/asset_categories/'+id+'/delete/');
  }

  //get asset category by id
  getAssetCategoryById(id:string):Observable<any>{
    return this.http.get(this.url+'master_data/asset_categories/'+id+'/detail/');
  }

  //add asset model
  addAssetModel(payload:any):Observable<any>{
    return this.http.post<any[]>(this.url+'master_data/add-asset_models/', payload)
  }
  
  //update asset model
  updateAssetModel(id:string, payload:any){
    return this.http.put(this.url+'master_data/asset_models/'+id+'/', payload);
  }

  //get all asset models
  getAllAssetModels():Observable<any>{
      return this.http.get(this.url+'master_data/asset-models/all/');
  }

  //delete asset model by id
  deleteAssetModelById(id:string):Observable<any>{
      return this.http.delete(this.url+'master_data/asset_models/'+id+'/delete/');
  }

  //get asset model by id
  getAssetModelById(id:string):Observable<any>{
    return this.http.get(this.url+'master_data/asset_models/'+id+'/detail/');
  }

  //add status
  addStatus(payload:any):Observable<any>{
    return this.http.post<any[]>(this.url+'master_data/add-status/', payload)
  }
  
  //update status
  updateStatus(id:string, payload:any){
    return this.http.put(this.url+'master_data/status/'+id+'/', payload);
  }

  //get all status
  getAllStatus():Observable<any>{
      return this.http.get(this.url+'master_data/statuses/all/');
  }

  //delete status by id
  deleteStatusById(id:string):Observable<any>{
      return this.http.delete(this.url+'master_data/status/'+id+'/delete/');
  }

  //get status by id
  getStatusById(id:string):Observable<any>{
    return this.http.get(this.url+'master_data/status/'+id+'/detail/');
  }

  //add supplier
  addSupplier(payload:any):Observable<any>{
    return this.http.post<any[]>(this.url+'master_data/suppliers/create/', payload)
  }
  
  //update supplier
  updateSupplier(id:string, payload:any){
    return this.http.put(this.url+'master_data/suppliers/'+id+'/update/', payload);
  }

  //get all suppliers
  getAllSuppliers():Observable<any>{
      return this.http.get(this.url+'master_data/suppliers/');
  }

  //delete supplier by id
  deleteSupplierById(id:string):Observable<any>{
      return this.http.delete(this.url+'master_data/suppliers/'+id+'/delete/');
  }

  //get supplier by id
  getSupplierById(id:string):Observable<any>{
    return this.http.get(this.url+'master_data/suppliers/'+id+'/');
  }

  //add company
  addCompany(payload:any):Observable<any>{
    return this.http.post<any[]>(this.url+'master_data/companies/create/', payload)
  }
  
  //update company
  updateCompany(id:string, payload:any){
    return this.http.put(this.url+'master_data/companies/'+id+'/update/', payload);
  }

  //get all companies
  getAllCompanies():Observable<any>{
      return this.http.get(this.url+'master_data/companies/');
  }

  //delete company by id
  deleteCompanyById(id:string):Observable<any>{
      return this.http.delete(this.url+'master_data/companies/'+id+'/delete/');
  }

  //get company by id
  getCompanyById(id:string):Observable<any>{
    return this.http.get(this.url+'master_data/companies/'+id+'/');
  }

  //get Project details by project type
  getProjectDetails(projectType:any): Observable<any>{
    return this.http.get(this.url+'pmo/api/get_projects_by_type/?project_type='+projectType)
  }
}
