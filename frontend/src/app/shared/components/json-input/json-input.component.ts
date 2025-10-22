import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';

@Component({
  selector: 'app-json-input',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './json-input.component.html',
  styleUrls: ['./json-input.component.scss'],
})
export class JsonInputComponent {
  @Input() label = 'JSON';
  @Input() placeholder = '{\n  "key": "value"\n}';
  @Input() value: any = {};
  @Output() valueChange = new EventEmitter<any>();

  text = '';
  error: string | null = null;

  ngOnInit(): void {
    this.text = this.format(this.value);
  }

  onChange(text: string) {
    this.text = text;
    try {
      const parsed = JSON.parse(text || '{}');
      this.error = null;
      this.value = parsed;
      this.valueChange.emit(parsed);
    } catch (e: any) {
      this.error = e?.message || 'JSON inválido';
    }
  }

  private format(obj: any): string {
    try {
      return JSON.stringify(obj ?? {}, null, 2);
    } catch {
      return '{}';
    }
  }
}
