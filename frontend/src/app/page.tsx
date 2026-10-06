import Image from "next/image";
import Link from "next/link";
import {
  ArrowRight,
  BookOpen,
  FileSearch,
  GraduationCap,
  MessageSquareText,
  Quote,
  ShieldCheck,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { LandingNav } from "@/components/landing/LandingNav";
import { ScrollReveal } from "@/components/landing/ScrollReveal";

const steps = [
  {
    num: "01",
    title: "Upload the source of truth",
    body: "Admins add circulars, handbooks, memos, and timetables. EduVault extracts the text and keeps the structure intact.",
  },
  {
    num: "02",
    title: "Ask in plain language",
    body: "Students and faculty type the same questions they’d ask a registrar — attendance rules, deadlines, leave policy, exam eligibility.",
  },
  {
    num: "03",
    title: "Read the answer with the page",
    body: "Every reply points back to a document, section, and page. If the archive doesn’t cover it, EduVault says so instead of inventing one.",
  },
];

const capabilities = [
  {
    icon: FileSearch,
    title: "Built for institutional PDFs",
    body: "Works with the messy pile universities already have — scanned circulars, Word memos, CSV schedules — not just neat blog posts.",
  },
  {
    icon: Quote,
    title: "Citations you can verify",
    body: "Answers include the exact source passage. Open the file, jump to the page, and confirm before you act on it.",
  },
  {
    icon: ShieldCheck,
    title: "Safe when uncertain",
    body: "Low-confidence retrieval stops generation. Better a clear “not found” than a confident wrong policy.",
  },
];

const audiences = [
  {
    role: "Students",
    detail: "Find attendance rules, exam policies, and deadlines without digging through email threads.",
  },
  {
    role: "Faculty",
    detail: "Quickly confirm handbook language before advising a student or drafting a notice.",
  },
  {
    role: "Admins",
    detail: "Keep one living archive. Upload once; the assistant stays current as documents change.",
  },
];

export default function HomePage() {
  return (
    <div id="top" className="min-h-screen bg-surface-primary text-text-primary">
      <LandingNav />

      {/* Hero — one composition: brand, line, support, CTAs, full-bleed GIF */}
      <section className="relative min-h-screen flex flex-col overflow-hidden">
        <div
          className="pointer-events-none absolute inset-0 landing-hero-atmosphere"
          aria-hidden
        />

        <div className="relative z-10 flex-1 flex flex-col justify-end pt-24 pb-8 sm:pb-10">
          <div className="max-w-6xl mx-auto w-full px-5 sm:px-6">
            <div className="max-w-2xl space-y-5 landing-hero-copy">
              <p className="text-accent font-semibold tracking-wide text-sm uppercase">
                EduVault
              </p>
              <h1 className="text-4xl sm:text-5xl md:text-[3.4rem] font-bold tracking-tight leading-[1.08] text-text-primary">
                Your university archive,
                <br className="hidden sm:block" /> answered with evidence.
              </h1>
              <p className="text-base sm:text-lg text-text-secondary max-w-xl leading-relaxed">
                Ask natural questions about circulars and handbooks. Get short
                answers tied to the document, section, and page — not guesses.
              </p>
              <div className="flex flex-wrap items-center gap-3 pt-1">
                <Link href="/register">
                  <Button size="lg" rightIcon={<ArrowRight className="w-4 h-4" />}>
                    Register
                  </Button>
                </Link>
                <Link href="/login">
                  <Button variant="outline" size="lg">
                    Login
                  </Button>
                </Link>
              </div>
            </div>
          </div>

          <div className="mt-10 sm:mt-12 w-full landing-hero-media">
            <div className="relative w-full aspect-[16/9] max-h-[min(52vh,900px)] border-y border-border bg-[#0f172a] overflow-hidden">
              <Image
                src="/eduvault-demo.gif"
                alt="EduVault answering a question about attendance with a cited source"
                fill
                unoptimized
                priority
                className="object-contain object-center"
                sizes="(max-width: 1600px) 100vw, 1600px"
              />
              <div
                className="absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-surface-primary to-transparent opacity-90 pointer-events-none"
                aria-hidden
              />
            </div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section
        id="how-it-works"
        className="relative border-t border-border py-20 sm:py-28"
      >
        <div className="max-w-6xl mx-auto px-5 sm:px-6">
          <ScrollReveal>
            <div className="max-w-xl mb-14">
              <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">
                How it works
              </h2>
              <p className="mt-3 text-text-secondary leading-relaxed">
                Three steps from a PDF on a shared drive to an answer you can
                trust in a meeting.
              </p>
            </div>
          </ScrollReveal>

          <ol className="space-y-0">
            {steps.map((step, i) => (
              <ScrollReveal key={step.num} delay={i * 90} variant="left">
                <li className="grid grid-cols-[4rem_1fr] sm:grid-cols-[5rem_1fr] gap-4 sm:gap-8 py-8 border-t border-border last:border-b">
                  <span className="font-mono text-accent text-sm pt-1">
                    {step.num}
                  </span>
                  <div>
                    <h3 className="text-xl font-semibold text-text-primary">
                      {step.title}
                    </h3>
                    <p className="mt-2 text-text-secondary leading-relaxed max-w-2xl">
                      {step.body}
                    </p>
                  </div>
                </li>
              </ScrollReveal>
            ))}
          </ol>
        </div>
      </section>

      {/* Features */}
      <section
        id="features"
        className="relative border-t border-border py-20 sm:py-28 bg-surface-secondary/40"
      >
        <div className="max-w-6xl mx-auto px-5 sm:px-6">
          <ScrollReveal>
            <div className="max-w-xl mb-14">
              <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">
                What stays different
              </h2>
              <p className="mt-3 text-text-secondary leading-relaxed">
                EduVault is a document assistant for policy — not a chatbot that
                improvises campus rules.
              </p>
            </div>
          </ScrollReveal>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-10 md:gap-8">
            {capabilities.map((item, i) => (
              <ScrollReveal key={item.title} delay={i * 100} variant="up">
                <div className="space-y-4">
                  <item.icon className="w-6 h-6 text-accent" strokeWidth={1.75} />
                  <h3 className="text-lg font-semibold text-text-primary">
                    {item.title}
                  </h3>
                  <p className="text-sm text-text-secondary leading-relaxed">
                    {item.body}
                  </p>
                </div>
              </ScrollReveal>
            ))}
          </div>
        </div>
      </section>

      {/* Audience */}
      <section
        id="audience"
        className="relative border-t border-border py-20 sm:py-28"
      >
        <div className="max-w-6xl mx-auto px-5 sm:px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-20 items-start">
            <ScrollReveal variant="left">
              <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">
                Who it's for
              </h2>
              <p className="mt-3 text-text-secondary leading-relaxed max-w-md">
                One knowledge layer for the people who live inside university
                paperwork every week.
              </p>
            </ScrollReveal>

            <div className="space-y-8">
              {audiences.map((item, i) => (
                <ScrollReveal key={item.role} delay={i * 80} variant="right">
                  <div className="border-l-2 border-accent pl-5">
                    <h3 className="text-base font-semibold text-text-primary">
                      {item.role}
                    </h3>
                    <p className="mt-1.5 text-sm text-text-secondary leading-relaxed">
                      {item.detail}
                    </p>
                  </div>
                </ScrollReveal>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Closing CTA */}
      <section className="relative border-t border-border py-20 sm:py-24">
        <div className="max-w-6xl mx-auto px-5 sm:px-6">
          <ScrollReveal variant="scale">
            <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-8">
              <div className="max-w-lg space-y-3">
                <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">
                  Start with your own documents
                </h2>
                <p className="text-text-secondary leading-relaxed">
                  Create an account, sign in, and open chat — or register an
                  admin seat to begin ingestion.
                </p>
              </div>
              <div className="flex flex-wrap gap-3">
                <Link href="/register">
                  <Button size="lg" leftIcon={<BookOpen className="w-4 h-4" />}>
                    Register
                  </Button>
                </Link>
                <Link href="/login">
                  <Button
                    variant="secondary"
                    size="lg"
                    leftIcon={<MessageSquareText className="w-4 h-4" />}
                  >
                    Login
                  </Button>
                </Link>
              </div>
            </div>
          </ScrollReveal>
        </div>
      </section>

      <footer className="border-t border-border py-10">
        <div className="max-w-6xl mx-auto px-5 sm:px-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
          <div className="flex items-center gap-2.5">
            <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-accent text-text-inverse">
              <GraduationCap className="w-4 h-4" />
            </span>
            <div>
              <p className="text-sm font-semibold text-text-primary">EduVault</p>
              <p className="text-2xs text-text-muted">
                University knowledge, grounded in sources
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-5 text-xs text-text-muted">
            <Link href="/login" className="hover:text-text-primary transition-colors">
              Login
            </Link>
            <Link
              href="/register"
              className="hover:text-text-primary transition-colors"
            >
              Register
            </Link>
            <Link href="/chat" className="hover:text-text-primary transition-colors">
              Chat
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
