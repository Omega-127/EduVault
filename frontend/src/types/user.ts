// ──────────────────────────────────────────────
// User Types
// ──────────────────────────────────────────────

export type UserRole = "student" | "faculty" | "admin";

export interface User {
  id: string;
  email: string;
  role: UserRole;
  created_at: string;
  is_active: boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  role?: UserRole;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}
