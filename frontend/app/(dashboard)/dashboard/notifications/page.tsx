'use client';

import * as React from 'react';
import { Bell, Check, Info, AlertTriangle, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface Notification {
  id: string;
  type: 'info' | 'warning' | 'success' | 'insight';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

const mockNotifications: Notification[] = [
  {
    id: '1',
    type: 'warning',
    title: 'Low Stock Alert',
    message: 'Wireless Bluetooth Headphones inventory is running low (15 units remaining)',
    timestamp: '2 hours ago',
    read: false,
  },
  {
    id: '2',
    type: 'success',
    title: 'Sales Target Reached',
    message: 'Congratulations! You have reached 90% of your monthly sales target',
    timestamp: '5 hours ago',
    read: false,
  },
  {
    id: '3',
    type: 'insight',
    title: 'Revenue Growth',
    message: 'Your revenue has increased by 12.5% compared to last week',
    timestamp: '1 day ago',
    read: false,
  },
  {
    id: '4',
    type: 'info',
    title: 'New Order',
    message: 'Order #ORD-12345 has been placed by Sarah Chen',
    timestamp: '2 days ago',
    read: true,
  },
  {
    id: '5',
    type: 'info',
    title: 'Customer Review',
    message: 'New 5-star review received for Organic Cotton T-Shirt',
    timestamp: '3 days ago',
    read: true,
  },
];

export default function NotificationsPage() {
  const [notifications, setNotifications] = React.useState(mockNotifications);

  const unreadCount = notifications.filter(n => !n.read).length;

  const markAsRead = (id: string) => {
    setNotifications(prev =>
      prev.map(n => (n.id === id ? { ...n, read: true } : n))
    );
  };

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  };

  const getIcon = (type: Notification['type']) => {
    switch (type) {
      case 'warning':
        return <AlertTriangle className="h-5 w-5" />;
      case 'success':
        return <Check className="h-5 w-5" />;
      case 'insight':
        return <TrendingUp className="h-5 w-5" />;
      default:
        return <Info className="h-5 w-5" />;
    }
  };

  const getColor = (type: Notification['type']) => {
    switch (type) {
      case 'warning':
        return 'text-amber-500 bg-amber-500/10';
      case 'success':
        return 'text-green-500 bg-green-500/10';
      case 'insight':
        return 'text-purple-500 bg-purple-500/10';
      default:
        return 'text-blue-500 bg-blue-500/10';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Notifications</h1>
          <p className="text-muted-foreground mt-1">
            Stay updated with your store activities
          </p>
        </div>
        <div className="flex items-center gap-2">
          {unreadCount > 0 && (
            <Button variant="outline" size="sm" onClick={markAllAsRead}>
              Mark all as read
            </Button>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total</p>
                <p className="text-2xl font-bold">{notifications.length}</p>
              </div>
              <Bell className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Unread</p>
                <p className="text-2xl font-bold">{unreadCount}</p>
              </div>
              <Badge variant="destructive" className="h-8 w-8 rounded-full flex items-center justify-center">
                {unreadCount}
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Read</p>
                <p className="text-2xl font-bold">{notifications.length - unreadCount}</p>
              </div>
              <Check className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Notifications List */}
      <Card>
        <CardHeader>
          <CardTitle>All Notifications</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="divide-y">
            {notifications.length === 0 ? (
              <div className="p-12 text-center">
                <Bell className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-sm text-muted-foreground">No notifications yet</p>
              </div>
            ) : (
              notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={cn(
                    'flex items-start gap-4 p-4 transition-colors hover:bg-muted/50',
                    !notification.read && 'bg-accent/5'
                  )}
                >
                  <div className={cn('rounded-full p-2', getColor(notification.type))}>
                    {getIcon(notification.type)}
                  </div>
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium leading-none">
                        {notification.title}
                      </p>
                      {!notification.read && (
                        <Badge variant="secondary" className="ml-2">
                          New
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {notification.message}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {notification.timestamp}
                    </p>
                  </div>
                  {!notification.read && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => markAsRead(notification.id)}
                    >
                      Mark as read
                    </Button>
                  )}
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
