"use client";

import { useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import type { LoginRequest, RegisterRequest, AuthResponse } from "@/types/user";

/**
 * Authentication hook.
 * Handles login, register, logout, and initial auth check.
 */
export function useAuth() {
  const router = useRouter();
  const {
    user,
    accessToken,
    isInitialized,
    isLoading,
    setUser,
    setAccessToken,
    setInitialized,
    setLoading,
    logout: clearAuth,
  } = useAuthStore();

  /** Check if there's a valid session on mount */
  const initialize = useCallback(async () => {
    const storedToken = localStorage.getItem("access_token");
    if (!storedToken) {
      setInitialized(true);
      return;
    }

    try {
      setAccessToken(storedToken);
      const { data } = await api.get("/auth/me");
      setUser(data);
    } catch {
      // Token is invalid or expired — clear it
      setAccessToken(null);
      setUser(null);
    } finally {
      setInitialized(true);
    }
  }, [setAccessToken, setInitialized, setUser]);

  useEffect(() => {
    if (!isInitialized) {
      initialize();
    }
  }, [isInitialized, initialize]);

  /** Log in with email and password */
  const login = async (credentials: LoginRequest) => {
    setLoading(true);
    try {
      const { data } = await api.post<AuthResponse>("/auth/login", credentials);
      setAccessToken(data.access_token);
      setUser(data.user);
      router.push("/chat");
    } finally {
      setLoading(false);
    }
  };

  /** Register a new account */
  const register = async (credentials: RegisterRequest) => {
    setLoading(true);
    try {
      const { data } = await api.post<AuthResponse>(
        "/auth/register",
        credentials
      );
      setAccessToken(data.access_token);
      setUser(data.user);
      router.push("/chat");
    } finally {
      setLoading(false);
    }
  };

  /** Log out and redirect to login */
  const logout = () => {
    clearAuth();
    router.push("/login");
  };

  return {
    user,
    accessToken,
    isAuthenticated: !!user,
    isAdmin: user?.role === "admin",
    isInitialized,
    isLoading,
    login,
    register,
    logout,
  };
}
