import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';

/**
 * JSON viewer component for displaying structured data.
 * Supports collapsible sections and syntax highlighting.
 */
@Component({
  selector: 'app-json-viewer',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './json-viewer.component.html',
  styleUrls: ['./json-viewer.component.scss'],
})
export class JsonViewerComponent {
  @Input() data: any = {};
  @Input() title = 'JSON';

  get displayText(): string {
    return JSON.stringify(this.data, null, 2);
  }

  copy(): void {
    navigator.clipboard.writeText(this.displayText).then(() => {
      alert('Copiado al portapapeles');
    });
  }
}
