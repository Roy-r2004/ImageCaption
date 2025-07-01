import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { bootstrapApplication } from '@angular/platform-browser';
import { provideHttpClient } from '@angular/common/http';
import { ApiService } from './api/api.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './app.html',
  styleUrls: ['./app.css'],
})
export class AppComponent implements OnInit {
  message: string = '';
  selectedFile: File | null = null;
  previewUrl: string | null = null;
  uploading: boolean = false;
  caption: string = '';
  history: { filename: string, caption: string, timestamp: string }[] = [];

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.loadHistory();
  }

  // Test FastAPI connection
  loadMessage(): void {
    this.apiService.getMessage().subscribe({
      next: (res) => this.message = res.message,
      error: (err) => console.error('API error:', err),
    });
  }

  // When user selects a file
  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) return;

    this.selectedFile = input.files[0];

    const reader = new FileReader();
    reader.onload = () => {
      this.previewUrl = reader.result as string;
    };
    reader.readAsDataURL(this.selectedFile);
  }

  // Upload the selected image to FastAPI and get caption
  uploadImage(): void {
    if (!this.selectedFile) return;

    this.uploading = true;
    this.caption = '';

    this.apiService.uploadImage(this.selectedFile).subscribe({
      next: (res) => {
        this.caption = res.caption;
        this.uploading = false;
        this.loadHistory(); // refresh history
      },
      error: (err) => {
        console.error('Upload failed:', err);
        this.uploading = false;
      }
    });
  }

  // Load saved caption history from backend
  loadHistory(): void {
    this.apiService.getHistory().subscribe({
      next: (res) => this.history = res,
      error: (err) => console.error('History load failed:', err),
    });
  }
}

// Bootstrap the standalone Angular app
bootstrapApplication(AppComponent, {
  providers: [provideHttpClient(), ApiService],
}).catch(err => console.error(err));
