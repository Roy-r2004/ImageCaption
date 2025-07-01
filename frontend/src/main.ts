// src/main.ts
import { bootstrapApplication } from '@angular/platform-browser';
import { AppComponent } from './app/app';
import { provideHttpClient } from '@angular/common/http';
import { ApiService } from './app/api/api.service';

bootstrapApplication(AppComponent, {
  providers: [provideHttpClient(), ApiService],
}).catch((err) => console.error(err));
