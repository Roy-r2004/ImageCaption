import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { bootstrapApplication } from '@angular/platform-browser';
import { provideHttpClient } from '@angular/common/http';
import { ApiService } from './api/api.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule,FormsModule],
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

  // New state for model and prompt
  selectedModel: string = 'blip'; // default
  prompt: string = 'Describe the image.';

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.loadHistory();
  }

  // Handle image selection
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

  // Upload image + form data
  uploadImage(): void {
    if (!this.selectedFile) return;

    this.uploading = true;
    this.caption = '';

    const formData = new FormData();
    formData.append('file', this.selectedFile);
    formData.append('model', this.selectedModel);

    if (this.selectedModel === 'blip2') {
      formData.append('prompt', this.prompt || 'Describe the image.');
    }

    this.apiService.uploadImage(formData).subscribe({
      next: (res) => {
        this.caption = res.caption;
        this.uploading = false;
        this.loadHistory();
      },
      error: (err) => {
        console.error('Upload failed:', err);
        this.message = 'Upload failed. Please try again.';
        this.uploading = false;
      }
    });
  }

  // Fetch previous caption history
  loadHistory(): void {
    this.apiService.getHistory().subscribe({
      next: (res) => this.history = res,
      error: (err) => console.error('History load failed:', err),
    });
  }
}

// Bootstrapping Angular
bootstrapApplication(AppComponent, {
  providers: [provideHttpClient(), ApiService],
}).catch(err => console.error(err));
