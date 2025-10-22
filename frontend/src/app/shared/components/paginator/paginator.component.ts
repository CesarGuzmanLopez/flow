import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';

/**
 * Reusable paginator component.
 * Emits page changes and integrates with data table and list views.
 */
@Component({
  selector: 'app-paginator',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './paginator.component.html',
  styleUrls: ['./paginator.component.scss'],
})
export class PaginatorComponent {
  @Input() total = 0;
  @Input() pageSize = 20;
  @Input() currentPage = 1;
  @Output() pageChange = new EventEmitter<number>();
  @Output() pageSizeChange = new EventEmitter<number>();

  pageSizeOptions = [10, 20, 50, 100];

  get totalPages(): number {
    return Math.ceil(this.total / this.pageSize);
  }

  get startIndex(): number {
    return (this.currentPage - 1) * this.pageSize + 1;
  }

  get endIndex(): number {
    return Math.min(this.currentPage * this.pageSize, this.total);
  }

  onPrevious(): void {
    if (this.currentPage > 1) {
      this.pageChange.emit(this.currentPage - 1);
    }
  }

  onNext(): void {
    if (this.currentPage < this.totalPages) {
      this.pageChange.emit(this.currentPage + 1);
    }
  }

  onPageSizeChange(size: number): void {
    this.pageSizeChange.emit(size);
  }

  canPrevious(): boolean {
    return this.currentPage > 1;
  }

  canNext(): boolean {
    return this.currentPage < this.totalPages;
  }
}
