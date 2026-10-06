"use client";

import { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/Button";
import {
  GraduationCap,
  Mail,
  Lock,
  ArrowRight,
  AlertCircle,
  UserPlus,
} from "lucide-react";

export default function RegisterPage() {
  const { register, isLoading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    try {
      await register({ email, password });
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "Registration failed. Please try again.";
      setError(message);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left panel — branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-surface-secondary border-r border-border flex-col justify-between p-12">
        <div>
          <div className="flex items-center gap-3 mb-16">
            <div className="w-10 h-10 rounded-xl bg-accent flex items-center justify-center">
              <GraduationCap className="w-6 h-6 text-text-inverse" />
            </div>
            <span className="text-2xl font-bold text-text-primary tracking-tight">
              EduVault
            </span>
          </div>

          <h1 className="text-4xl font-bold text-text-primary leading-tight mb-4">
            Join EduVault
            <span className="text-accent">.</span>
          </h1>
          <p className="text-lg text-text-secondary max-w-md">
            Create your account and start exploring your university&apos;s
            institutional knowledge base with AI-powered search.
          </p>
        </div>

        <div className="space-y-4">
          {[
            "Instant answers from official university documents",
            "Every answer includes source citations",
            "Secure, role-based access for students and faculty",
          ].map((feature, idx) => (
            <div
              key={idx}
              className="flex items-center gap-3 text-sm text-text-secondary"
            >
              <div className="w-1.5 h-1.5 rounded-full bg-accent flex-shrink-0" />
              <span>{feature}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Right panel — registration form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-surface-primary">
        <div className="w-full max-w-md space-y-8">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <div className="w-10 h-10 rounded-xl bg-accent flex items-center justify-center">
              <GraduationCap className="w-6 h-6 text-text-inverse" />
            </div>
            <span className="text-2xl font-bold text-text-primary tracking-tight">
              EduVault
            </span>
          </div>

          <div>
            <h2 className="text-2xl font-bold text-text-primary">
              Create your account
            </h2>
            <p className="text-sm text-text-muted mt-1">
              Use your university email to get started
            </p>
          </div>

          {/* Error */}
          {error && (
            <div className="flex items-center gap-2 p-3 rounded-lg bg-danger-subtle text-danger text-sm animate-slide-up">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Email */}
            <div className="space-y-2">
              <label
                htmlFor="email"
                className="text-sm font-medium text-text-secondary"
              >
                University Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@university.edu"
                  required
                  className="input-base pl-11"
                />
              </div>
            </div>

            {/* Password */}
            <div className="space-y-2">
              <label
                htmlFor="password"
                className="text-sm font-medium text-text-secondary"
              >
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="At least 8 characters"
                  required
                  minLength={8}
                  className="input-base pl-11"
                />
              </div>
            </div>

            {/* Confirm password */}
            <div className="space-y-2">
              <label
                htmlFor="confirmPassword"
                className="text-sm font-medium text-text-secondary"
              >
                Confirm Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
                <input
                  id="confirmPassword"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter your password"
                  required
                  className="input-base pl-11"
                />
              </div>
            </div>

            <Button
              type="submit"
              className="w-full"
              size="lg"
              isLoading={isLoading}
              leftIcon={<UserPlus className="w-4 h-4" />}
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Create Account
            </Button>
          </form>

          <p className="text-sm text-text-muted text-center">
            Already have an account?{" "}
            <Link
              href="/login"
              className="text-accent hover:text-accent-hover font-medium transition-colors"
            >
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
