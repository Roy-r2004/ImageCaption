import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private BASE_URL = 'http://localhost:8000/api';

  constructor(private http: HttpClient) {}

  getMessage(): Observable<any> {
    return this.http.get(`${this.BASE_URL}/message`);
  }

  uploadImage(file: File, model: string): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('model', model);
    return this.http.post(`${this.BASE_URL}/upload-image`, formData);
  }

  getHistory(): Observable<any[]> {
    return this.http.get<any[]>(`${this.BASE_URL}/history`);
  }
}
