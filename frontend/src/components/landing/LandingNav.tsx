"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { GraduationCap, Menu, X } from "lucide-react";
import { Button } from "@/components/ui/Button";

const links = [
  { href: "#how-it-works", label: "How it works" },
  { href: "#features", label: "Features" },
  { href: "#audience", label: "Who it's for" },
];

export function LandingNav() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 16);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <header
      className={`fixed top-0 inset-x-0 z-50 transition-all duration-300 ${
        scrolled || open
          ? "bg-surface-primary/95 border-b border-border backdrop-blur-sm"
          : "bg-transparent border-b border-transparent"
      }`}
    >
      <div className="max-w-6xl mx-auto px-5 sm:px-6 h-16 flex items-center justify-between">
        <a href="#top" className="flex items-center gap-2.5 group">
          <span className="flex items-center justify-center w-9 h-9 rounded-lg bg-accent text-text-inverse">
            <GraduationCap className="w-5 h-5" />
          </span>
          <span className="text-lg font-bold tracking-tight text-text-primary group-hover:text-accent transition-colors">
            EduVault
          </span>
        </a>

        <nav className="hidden md:flex items-center gap-8 text-sm text-text-secondary">
          {links.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="hover:text-text-primary transition-colors"
            >
              {link.label}
            </a>
          ))}
        </nav>

        <div className="hidden md:flex items-center gap-2">
          <Link href="/login">
            <Button variant="ghost" size="sm">
              Login
            </Button>
          </Link>
          <Link href="/register">
            <Button size="sm">Register</Button>
          </Link>
        </div>

        <button
          type="button"
          className="md:hidden p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-tertiary transition-colors"
          aria-label={open ? "Close menu" : "Open menu"}
          onClick={() => setOpen((v) => !v)}
        >
          {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {open && (
        <div className="md:hidden border-t border-border bg-surface-primary px-5 py-4 space-y-1">
          {links.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="block px-3 py-2.5 rounded-lg text-sm text-text-secondary hover:text-text-primary hover:bg-surface-tertiary transition-colors"
              onClick={() => setOpen(false)}
            >
              {link.label}
            </a>
          ))}
          <div className="pt-3 flex gap-2">
            <Link href="/login" className="flex-1" onClick={() => setOpen(false)}>
              <Button variant="outline" size="md" className="w-full">
                Login
              </Button>
            </Link>
            <Link
              href="/register"
              className="flex-1"
              onClick={() => setOpen(false)}
            >
              <Button size="md" className="w-full">
                Register
              </Button>
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
