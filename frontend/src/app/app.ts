import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { bootstrapApplication } from '@angular/platform-browser';
import { provideHttpClient } from '@angular/common/http';
import { ApiService } from './api/api.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.html',
  styleUrls: ['./app.css'],
})
export class AppComponent implements OnInit {
  // 📦 Upload state
  selectedFile: File | null = null;
  previewUrl: string | null = null;
  uploading: boolean = false;

  // 📄 Output
  caption: string = '';
  message: string = '';

  // 🧠 Model + prompt + mode
  selectedModel: string = 'blip';
  prompt: string = 'Describe the image.';
  mode: 'caption' | 'title' = 'caption';
   Math = Math;

  // 🗂️ History data
  history: { filename: string; caption: string; timestamp: string }[] = [];

  // 🔍 Table features
  filter: string = '';
  pageSize: number = 5;
  page: number = 1;

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.loadHistory();
  }

  // 🖼️ Image preview
  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (!input.files?.length) return;

    this.selectedFile = input.files[0];

    const reader = new FileReader();
    reader.onload = () => {
      this.previewUrl = reader.result as string;
    };
    reader.readAsDataURL(this.selectedFile);
  }

  // 🚀 Main upload handler
  upload(): void {
    if (!this.selectedFile) return;

    this.uploading = true;
    this.caption = '';
    this.message = '';

    const formData = new FormData();
    formData.append('file', this.selectedFile);

    if (this.mode === 'caption') {
      formData.append('model', this.selectedModel);
      formData.append('prompt', this.prompt || 'Describe the image.');
      this.uploadCaption(formData);
    } else {
      this.uploadTitle(formData);
    }
  }

  // 🎯 Upload caption
  private uploadCaption(formData: FormData): void {
    this.apiService.uploadImage(formData).subscribe({
      next: (res) => {
        this.caption = res.caption;
        this.uploading = false;
        this.loadHistory(); // update table
      },
      error: (err) => {
        console.error('❌ Caption upload failed:', err);
        this.message = 'Upload failed. Please try again.';
        this.uploading = false;
      },
    });
  }

  // 🎯 Upload title
  private uploadTitle(formData: FormData): void {
    this.apiService.generateTitle(formData).subscribe({
      next: (res) => {
        this.caption = res.title;
        this.uploading = false;
      },
      error: (err) => {
        console.error('❌ Title generation failed:', err);
        this.message = 'Failed to generate title.';
        this.uploading = false;
      },
    });
  }

  // 📜 Load caption history
  loadHistory(): void {
    this.apiService.getHistory().subscribe({
      next: (res) => (this.history = res),
      error: (err) => console.error('History fetch failed:', err),
    });
  }

  // 🔍 Filter + paginate history table
  filteredHistory(): any[] {
    const filtered = this.filter
      ? this.history.filter(item =>
          item.caption.toLowerCase().includes(this.filter.toLowerCase())
        )
      : this.history;

    const start = (this.page - 1) * this.pageSize;
    return filtered.slice(start, start + this.pageSize);
  }

  // 📄 Total count for pagination
  get filteredCount(): number {
    return this.filter
      ? this.history.filter(item =>
          item.caption.toLowerCase().includes(this.filter.toLowerCase())
        ).length
      : this.history.length;
  }
}

// 🚀 Bootstrap Angular app
bootstrapApplication(AppComponent, {
  providers: [provideHttpClient(), ApiService],
}).catch((err) => console.error(err));
