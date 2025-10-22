import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
} from '@angular/core';
import { RouterLink } from '@angular/router';

export interface TableColumn {
  key: string;
  label: string;
  type?: 'text' | 'number' | 'date' | 'link' | 'badge' | 'actions';
  linkPrefix?: string; // e.g. '/flows/'
  badgeClass?: (value: any) => string;
  actions?: { label: string; action: string }[]; // for actions type
}

/**
 * Reusable table component for displaying lists of data.
 * Supports sorting, pagination, and custom cell rendering.
 */
@Component({
  selector: 'app-data-table',
  standalone: true,
  imports: [CommonModule, RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './data-table.component.html',
  styleUrls: ['./data-table.component.scss'],
})
export class DataTableComponent {
  @Input() columns: TableColumn[] = [];
  @Input() data: any[] = [];
  @Input() loading = false;
  @Input() emptyMessage = 'No hay datos';

  @Output() rowClick = new EventEmitter<any>();
  @Output() actionClick = new EventEmitter<{ action: string; row: any }>();

  onRowClick(row: any) {
    this.rowClick.emit(row);
  }

  onAction(action: string, row: any, event: Event) {
    event.stopPropagation();
    this.actionClick.emit({ action, row });
  }

  getCellValue(row: any, col: TableColumn): any {
    const keys = col.key.split('.');
    let value = row;
    for (const k of keys) {
      value = value?.[k];
      if (value === undefined) break;
    }
    return value;
  }

  formatDate(value: any): string {
    if (!value) return '-';
    try {
      return new Date(value).toLocaleString();
    } catch {
      return value;
    }
  }

  getBadgeClass(col: TableColumn, value: any): string {
    if (col.badgeClass) return col.badgeClass(value);
    return 'badge';
  }
}
