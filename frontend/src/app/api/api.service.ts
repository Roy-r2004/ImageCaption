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

  uploadImage(formData: FormData): Observable<any> {
    return this.http.post(`${this.BASE_URL}/upload-image`, formData);
  }

  getHistory(): Observable<any[]> {
    return this.http.get<any[]>(`${this.BASE_URL}/history`);
  }

  /**
   * 🆕 Upload image and get title
   */
  generateTitle(formData: FormData): Observable<any> {
    return this.http.post(`${this.BASE_URL}/generate-title`, formData);
  }

  /**
   * 🧠 Qwen image analysis: title, tags, desc, specs
   */
  analyzeWithQwen(formData: FormData): Observable<any> {
    return this.http.post(`${this.BASE_URL}/qwen-analyze`, formData);
  }
}
