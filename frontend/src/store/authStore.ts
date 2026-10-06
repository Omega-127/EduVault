import { create } from "zustand";
import type { User } from "@/types/user";

interface AuthState {
  /** Current authenticated user, or null */
  user: User | null;
  /** JWT access token stored in memory */
  accessToken: string | null;
  /** Whether initial auth check is complete */
  isInitialized: boolean;
  /** Whether a login/register request is in progress */
  isLoading: boolean;

  setUser: (user: User | null) => void;
  setAccessToken: (token: string | null) => void;
  setInitialized: (initialized: boolean) => void;
  setLoading: (loading: boolean) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  accessToken: null,
  isInitialized: false,
  isLoading: false,

  setUser: (user) => set({ user }),

  setAccessToken: (token) => {
    // Persist to localStorage for axios interceptor
    if (typeof window !== "undefined") {
      if (token) {
        localStorage.setItem("access_token", token);
      } else {
        localStorage.removeItem("access_token");
      }
    }
    set({ accessToken: token });
  },

  setInitialized: (initialized) => set({ isInitialized: initialized }),
  setLoading: (loading) => set({ isLoading: loading }),

  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
    }
    set({ user: null, accessToken: null });
  },
}));
