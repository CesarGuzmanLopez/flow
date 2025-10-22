import { CommonModule } from '@angular/common';
import {
  Component,
  DestroyRef,
  Input,
  OnChanges,
  OnDestroy,
  WritableSignal,
  inject,
  signal,
} from '@angular/core';
import { SseMessage, SseService } from '../../../services/sse.service';

@Component({
  selector: 'app-sse-log-viewer',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './sse-log-viewer.component.html',
  styleUrls: ['./sse-log-viewer.component.scss'],
})
export class SseLogViewerComponent implements OnChanges, OnDestroy {
  private readonly sse = inject(SseService);
  private readonly destroyRef = inject(DestroyRef);

  @Input() stepExecutionId?: string | number;

  lines: WritableSignal<string[]> = signal([]);
  status: WritableSignal<string> = signal('idle');

  private source?: EventSource;

  ngOnChanges(): void {
    this.reset();
    if (!this.stepExecutionId) return;
    this.status.set('connecting');
    this.source = this.sse.openStepExecutionLogs(
      this.stepExecutionId,
      (msg: SseMessage) => this.onSse(msg),
      () => this.status.set('error')
    );
    this.status.set('streaming');
  }

  ngOnDestroy(): void {
    if (this.stepExecutionId) this.sse.close(this.stepExecutionId);
    this.source?.close();
  }

  clear(): void {
    this.lines.set([]);
  }

  private reset(): void {
    if (this.stepExecutionId) this.sse.close(this.stepExecutionId);
    this.source?.close();
    this.lines.set([]);
    this.status.set('idle');
  }

  private onSse(msg: SseMessage) {
    if (!msg) return;
    if (msg.event === 'log' && msg.data?.line) {
      this.append(`[${msg.data.at ?? ''}] ${msg.data.line}`);
    } else if (msg.event === 'start') {
      this.append('--- execution started ---');
    } else if (msg.event === 'end') {
      this.append('--- execution ended ---');
      this.status.set('ended');
    }
  }

  private append(line: string) {
    const arr = this.lines();
    arr.push(line);
    this.lines.set([...arr]);
    setTimeout(() => {
      const el = document.getElementById('sse-log-scroll');
      if (el) el.scrollTop = el.scrollHeight;
    }, 0);
  }
}
