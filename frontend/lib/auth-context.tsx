"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { User, TokenResponse, apiRequest, setAccessToken, getAccessToken, coordinateTokenRefresh } from "./api";

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
      if (!token) {
        // Attempt single coordinated refresh on initial app load
        const freshToken = await coordinateTokenRefresh();
        if (freshToken) {
          const userData = await apiRequest<User>("/auth/me");
          setUser(userData);
          return;
        }
        setUser(null);
        return;
      }
      const userData = await apiRequest<User>("/auth/me");
      setUser(userData);
    } catch {
      setAccessToken(null);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshUser();
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const data = await apiRequest<TokenResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setAccessToken(data.access_token);
      setUser(data.user);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await apiRequest("/auth/logout", { method: "POST" });
    } catch (e) {
      console.error("Logout error", e);
    } finally {
      setAccessToken(null);
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
