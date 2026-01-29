import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';
import { environment } from '../../environment';
import { User} from '../models/user';

@Injectable({
  providedIn: 'root'
})
export class UserService {
  private readonly url=environment.apiUrl; 
  private token = localStorage.getItem('access_token'); 

  // private headers = new HttpHeaders({
  //   'Authorization': `Bearer ${this.token}`
  // });

  constructor(private http:HttpClient) { }

   getMaintainUsers():Observable<any>{
    const headers = new HttpHeaders({
    'Authorization': `Bearer ${this.token}`
  });
    return this.http.get<User[]>(this.url+'user_management/get_users/')
  }

  createUser(user:User){ 
    return this.http.post(this.url+'user_management/create_user/', user);
  }

   getUserDataById(userId:string):Observable<any>{
    return this.http.get(this.url+'user_management/get_users/'+userId+'/');
  }

    updateUser(userId:string,obj:any){
      return this.http.put(this.url+'user_management/edit_user/'+userId+'/',obj);
    }

    deleteUser(userId: string): Observable<any> {
      return this.http.delete(this.url + 'user_management/delete_user/'+userId+'/');
    }

  getAssignRoles():Observable<any>{
    return this.http.get(this.url+'user_management/get_user_role_assignments/');
  }
  getAssignRolesByUserId(user_id:string):Observable<any>{
    return this.http.get(this.url+'user_management/get_user_role_assign_byid/'+user_id);
  }
  
  // assignUserRoles(user:User){ 
  //   return this.http.post('http://127.0.0.1:8080/user_management/user_management/user_role_assign/', user);
  //   }
  assignUserRoles(user:User){ 
    return this.http.post(this.url+'user_management/user_role_assign/', user);
    }

  updateAssignUserRoles(roles:any,userId:string){ 
      return this.http.patch(this.url+'user_management/edit_user_role_assign/'+userId+'/', roles);
      }

    getRoles():Observable<any>{
      return this.http.get(this.url+'user_management/get_roles/');
    }
  

}
