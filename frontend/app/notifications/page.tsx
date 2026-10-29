"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import AppShell from "@/components/layout/AppShell";
import { api, NotificationItem } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { 
  Bell, 
  CheckCircle, 
  Clock, 
  Filter, 
  ExternalLink, 
  CheckCheck, 
  AlertTriangle, 
  Info, 
  ShieldAlert, 
  FileText 
} from "lucide-react";

export default function NotificationsPage() {
  const { user, isLoading: isAuthLoading } = useAuth();
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isMarkingAll, setIsMarkingAll] = useState(false);

  const fetchNotifications = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const items = await api.listNotifications(unreadOnly ? { is_read: false } : {});
      setNotifications(items);
    } catch (err: any) {
      setError(err.message || "Failed to load notifications.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!isAuthLoading && user) {
      fetchNotifications();
    }
  }, [isAuthLoading, user, unreadOnly]);

  const handleMarkAsRead = async (id: string) => {
    try {
      await api.markNotificationRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
    } catch (err: any) {
      console.error("Failed to mark notification read", err);
    }
  };

  const handleMarkAllRead = async () => {
    setIsMarkingAll(true);
    try {
      await api.markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch (err: any) {
      console.error("Failed to mark all as read", err);
    } finally {
      setIsMarkingAll(false);
    }
  };

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case "CONFLICT_DETECTED":
        return <AlertTriangle className="w-4 h-4 text-amber-600" />;
      case "RESPONSE_SUBMITTED":
        return <FileText className="w-4 h-4 text-blue-600" />;
      case "STATUS_TRANSITION":
        return <ShieldAlert className="w-4 h-4 text-purple-600" />;
      case "CORRECTION_APPLIED":
        return <CheckCircle className="w-4 h-4 text-emerald-600" />;
      default:
        return <Info className="w-4 h-4 text-stone-600" />;
    }
  };

  return (
    <AppShell>
      <div className="space-y-6 max-w-5xl mx-auto pb-12">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-stone-200">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-[#475569]">Institutional notifications</span>
              <span className="text-xs text-stone-400">•</span>
              <span className="text-xs text-stone-500">System notices</span>
            </div>
            <h1 className="text-xl font-bold text-stone-900 mt-0.5">Workflow notifications</h1>
            <p className="text-xs text-stone-600 mt-1">
              Real-time audit alerts for discrepancy detection, responses, and correction lifecycle events.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setUnreadOnly(!unreadOnly)}
              className={`px-3 py-1.5 text-xs font-medium rounded border transition-colors ${
                unreadOnly
                  ? "bg-stone-900 text-white border-stone-900"
                  : "bg-white text-stone-700 border-stone-300 hover:bg-stone-50"
              }`}
            >
              {unreadOnly ? "Showing unread only" : "Filter unread"}
            </button>

            <button
              onClick={handleMarkAllRead}
              disabled={isMarkingAll || notifications.every((n) => n.is_read)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded border border-stone-300 bg-white text-stone-700 hover:bg-stone-50 disabled:opacity-50 transition-colors shadow-sm"
            >
              <CheckCheck className="w-3.5 h-3.5 text-stone-600" />
              <span>Mark all as read</span>
            </button>
          </div>
        </div>

        {/* Loading and Error */}
        {isLoading && (
          <div className="bg-white rounded-lg border border-stone-200 p-12 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-2 border-stone-300 border-t-stone-800"></div>
            <p className="mt-3 text-sm text-stone-600">Loading notifications...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-red-800">
            <p className="text-sm font-semibold">Failed to load notifications</p>
            <p className="text-xs mt-1 text-red-700">{error}</p>
            <button
              onClick={fetchNotifications}
              className="mt-3 px-3 py-1 bg-red-100 hover:bg-red-200 text-red-800 text-xs font-medium rounded border border-red-300"
            >
              Retry
            </button>
          </div>
        )}

        {/* Notifications List */}
        {!isLoading && !error && (
          <div className="bg-white rounded-lg border border-stone-200 divide-y divide-stone-100 shadow-sm overflow-hidden">
            {notifications.length === 0 ? (
              <div className="p-12 text-center">
                <Bell className="w-8 h-8 text-stone-300 mx-auto mb-2" />
                <h3 className="text-sm font-semibold text-stone-800">No notifications</h3>
                <p className="text-xs text-stone-500 mt-1">
                  {unreadOnly ? "You have no unread notifications." : "There are no notifications in your queue."}
                </p>
              </div>
            ) : (
              notifications.map((notif) => (
                <div
                  key={notif.id}
                  className={`p-4 transition-colors flex items-start justify-between gap-4 ${
                    notif.is_read ? "bg-white hover:bg-stone-50/50" : "bg-amber-50/20 hover:bg-amber-50/30"
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className="p-2 rounded bg-stone-100 border border-stone-200 flex-shrink-0 mt-0.5">
                      {getEventIcon(notif.event_type)}
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-stone-900">{notif.title}</span>
                        {!notif.is_read && (
                          <span className="w-2 h-2 rounded-full bg-amber-600 inline-block"></span>
                        )}
                        <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-100 text-[#475569] tabular-nums">
                          {notif.event_type.toLowerCase().replace(/_/g, " ")}
                        </span>
                      </div>
                      <p className="text-xs text-stone-700 leading-relaxed">{notif.message}</p>
                      <div className="flex items-center gap-3 text-[11px] text-stone-500 pt-1">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {new Date(notif.created_at).toLocaleString()}
                        </span>
                        {notif.related_resource_type === "FINDING" && (
                          <Link
                            href={`/findings/${notif.related_resource_id}`}
                            className="text-amber-700 hover:text-amber-800 font-medium inline-flex items-center gap-1 underline"
                          >
                            <span>Open finding</span>
                            <ExternalLink className="w-3 h-3" />
                          </Link>
                        )}
                      </div>
                    </div>
                  </div>

                  {!notif.is_read && (
                    <button
                      onClick={() => handleMarkAsRead(notif.id)}
                      className="text-xs text-stone-500 hover:text-stone-800 px-2 py-1 rounded border border-stone-200 hover:bg-stone-100 flex-shrink-0 transition-colors"
                    >
                      Mark read
                    </button>
                  )}
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </AppShell>
  );
}
