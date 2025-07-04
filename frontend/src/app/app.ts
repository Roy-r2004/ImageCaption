import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { bootstrapApplication } from '@angular/platform-browser';
import { provideHttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { ApiService } from './api/api.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.html',
  styleUrls: ['./app.css'],
})
export class AppComponent implements OnInit {
  message: string = '';
  selectedFile: File | null = null;
  previewUrl: string | null = null;
  uploading: boolean = false;
  caption: string = '';
  product: string = '';
  history: { filename: string; caption: string; timestamp: string }[] = [];

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.loadHistory();
  }

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

  uploadImage(): void {
    if (!this.selectedFile) return;

    this.uploading = true;
    this.caption = '';

    this.apiService.uploadImage(this.selectedFile, this.product).subscribe({
      next: (res) => {
        this.caption = res.caption;
        this.uploading = false;
        this.loadHistory();
      },
      error: (err) => {
        console.error('Upload failed:', err);
        this.uploading = false;
      },
    });
  }

  loadHistory(): void {
    this.apiService.getHistory().subscribe({
      next: (res) => (this.history = res),
      error: (err) => console.error('History load failed:', err),
    });
  }
}

bootstrapApplication(AppComponent, {
  providers: [provideHttpClient(), ApiService],
}).catch((err) => console.error(err));