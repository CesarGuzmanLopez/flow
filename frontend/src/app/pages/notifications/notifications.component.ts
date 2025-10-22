import { CommonModule } from '@angular/common';
import { Component, inject, OnDestroy, OnInit, signal } from '@angular/core';
import { interval, Subscription } from 'rxjs';
import { NotificationsService } from '../../services/notifications.service';

interface Notification {
  id: number;
  type: string;
  title: string;
  message: string;
  read: boolean;
  created_at: Date;
  priority: 'low' | 'normal' | 'high' | 'urgent';
}

@Component({
  selector: 'app-notifications',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './notifications.component.html',
  styleUrls: ['./notifications.component.scss'],
})
export class NotificationsComponent implements OnInit, OnDestroy {
  private readonly notificationsService = inject(NotificationsService);

  notifications = signal<Notification[]>([]);
  loading = signal(false);
  error = signal<string | null>(null);
  unreadCount = signal(0);
  activeFilter = signal<'all' | 'unread'>('all');
  filteredNotifications = signal<Notification[]>([]);
  private pollSubscription?: Subscription;

  ngOnInit(): void {
    this.loadNotifications();
    // Poll every 10 seconds (simulating backend updates)
    this.pollSubscription = interval(10000).subscribe(() => {
      this.loadNotifications();
    });
  }

  ngOnDestroy(): void {
    this.pollSubscription?.unsubscribe();
  }

  loadNotifications(): void {
    this.loading.set(true);
    this.error.set(null);

    this.notificationsService.listNotifications().subscribe({
      next: (data) => {
        const list = (data || []).map((n: any) => ({
          ...n,
          created_at: new Date(n.created_at),
        }));
        this.notifications.set(list);
        this.applyFilter();
        this.updateUnreadCount();
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err?.message || 'Error loading notifications');
        this.loading.set(false);
      },
    });
  }

  applyFilter(): void {
    const filter = this.activeFilter();
    const list = this.notifications();
    this.filteredNotifications.set(
      filter === 'unread' ? list.filter((n) => !n.read) : list
    );
  }

  updateUnreadCount(): void {
    const unread = this.notifications().filter((n) => !n.read).length;
    this.unreadCount.set(unread);
  }

  onRowClick(notification: Notification): void {
    this.markAsRead(notification.id);
  }

  markAsRead(id: number): void {
    this.notificationsService.markAsRead(id).subscribe({
      next: () => {
        const updated = this.notifications().map((n) =>
          n.id === id ? { ...n, read: true } : n
        );
        this.notifications.set(updated);
        this.applyFilter();
        this.updateUnreadCount();
      },
      error: (err) => this.error.set(err?.message || 'Error marking as read'),
    });
  }

  markAllAsRead(): void {
    this.notificationsService.markAllAsRead().subscribe({
      next: () => {
        const updated = this.notifications().map((n) => ({ ...n, read: true }));
        this.notifications.set(updated);
        this.applyFilter();
        this.updateUnreadCount();
      },
      error: (err) =>
        this.error.set(err?.message || 'Error marking all as read'),
    });
  }

  deleteNotification(id: number): void {
    this.notificationsService.deleteNotification(id).subscribe({
      next: () => {
        const updated = this.notifications().filter((n) => n.id !== id);
        this.notifications.set(updated);
        this.applyFilter();
      },
      error: (err) =>
        this.error.set(err?.message || 'Error deleting notification'),
    });
  }

  setFilter(filter: 'all' | 'unread'): void {
    this.activeFilter.set(filter);
    this.applyFilter();
  }
}
