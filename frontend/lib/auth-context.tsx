"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import {
  User,
  TokenResponse,
  apiRequest,
  setAccessToken,
  getAccessToken,
  coordinateTokenRefresh,
  hasSessionActive,
  setSessionActive,
  onSessionExpired,
  notifySessionExpired
} from "./api";

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  hasPermission: (permissionCode: string) => boolean;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = async () => {
    try {
      const token = getAccessToken();
      if (token) {
        const userData = await apiRequest<User>("/auth/me");
        setUser(userData);
        return;
      }

      // If no active session indicator exists, do NOT make unnecessary /auth/refresh calls
      if (!hasSessionActive()) {
        setUser(null);
        return;
      }

      // Attempt coordinated refresh only when an active session is expected
      const freshToken = await coordinateTokenRefresh();
      if (freshToken) {
        const userData = await apiRequest<User>("/auth/me");
        setUser(userData);
        return;
      }

      // Refresh failed or revoked: clear stale local state cleanly
      setAccessToken(null);
      setSessionActive(false);
      setUser(null);
    } catch {
      setAccessToken(null);
      setSessionActive(false);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshUser();

    // Subscribe to session expiration events triggered by 401s across the app
    const unsubscribe = onSessionExpired(() => {
      setUser(null);
      setIsLoading(false);
      if (typeof window !== "undefined") {
        const publicPaths = ["/login", "/register", "/verify", "/forgot-password", "/reset-password"];
        const pathname = window.location.pathname;
        const isPublic = publicPaths.some((p) => pathname === p || pathname.startsWith(p + "/"));
        if (!isPublic) {
          window.location.href = "/login?session_expired=1";
        }
      }
    });

    return unsubscribe;
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const data = await apiRequest<TokenResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setAccessToken(data.access_token);
      setSessionActive(true);
      setUser(data.user);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await apiRequest("/auth/logout", { method: "POST" });
    } catch {
      // Gracefully clear local session regardless of network error
    } finally {
      setAccessToken(null);
      setSessionActive(false);
      setUser(null);
    }
  };

  const hasPermission = (permissionCode: string): boolean => {
    if (!user) return false;
    if (user.roles.includes("PLATFORM_ADMIN") || user.roles.includes("AICTE_ADMIN")) {
      return true;
    }
    return user.permissions.includes(permissionCode);
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout, hasPermission, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
