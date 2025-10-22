import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';

/**
 * Reusable modal dialog component.
 * Provides overlay and centered content with header/footer slots.
 */
@Component({
  selector: 'app-modal',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './modal.component.html',
  styleUrls: ['./modal.component.scss'],
})
export class ModalComponent {
  @Input() title = '';
  @Input() visible = false;
  @Input() size: 'small' | 'medium' | 'large' = 'medium';

  @Output() close = new EventEmitter<void>();

  onClose() {
    this.close.emit();
  }

  onBackdropClick() {
    this.onClose();
  }

  onContentClick(event: Event) {
    event.stopPropagation();
  }
}
