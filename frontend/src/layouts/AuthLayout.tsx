import { BellRing, ClipboardCheck, Milestone } from "lucide-react";
import { Outlet } from "react-router";

import { AppLogo } from "@/components/AppLogo";
import { useUiScale } from "@/hooks/useUiScale";

const BENEFITS = [
  {
    icon: ClipboardCheck,
    text: "Every quotation, design revision, and approval is recorded with its date, time, and user.",
  },
  {
    icon: BellRing,
    text: "Notifications and reminders go out when a decision is left pending.",
  },
  {
    icon: Milestone,
    text: "Clients and staff follow each project from request to turnover.",
  },
];

/** A line drawing of a counter with dimension lines: the "blueprint" of the sign-in panel. */
function BlueprintDrawing() {
  return (
    <svg
      viewBox="0 0 520 300"
      aria-hidden="true"
      className="pointer-events-none absolute -right-16 bottom-10 w-[34rem] max-w-none text-white/25"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
    >
      <rect x="80" y="40" width="360" height="150" rx="3" />
      <rect x="130" y="70" width="260" height="60" rx="3" strokeDasharray="6 5" />
      <path d="M120 190v70h280v-70" />
      <path d="M110 180h300v12H110z" />
      <path d="M170 204h60v44h-60zM250 204h60v44h-60zM330 204h50v44h-50z" />
      <path d="M80 18h360M80 10v16M440 10v16" />
      <path d="M470 40v150M462 40h16M462 190h16" />
      <path d="M120 284h280M120 276v16M400 276v16" />
    </svg>
  );
}

/** The sign-in screens: a blueprint-blue panel on the left, the form on the right. */
export function AuthLayout() {
  useUiScale("auth");
  return (
    <div className="grid min-h-dvh bg-card lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)]">
      <aside className="blueprint-grid relative hidden flex-col justify-between overflow-hidden bg-primary p-12 text-white lg:flex">
        <AppLogo variant="inverse" size="lg" />
        <BlueprintDrawing />
        <div className="relative max-w-md">
          <p className="text-3xl leading-tight font-semibold tracking-tight">
            Client coordination for custom fabrication projects
          </p>
          <ul className="mt-8 flex flex-col gap-5">
            {BENEFITS.map(({ icon: Icon, text }) => (
              <li key={text} className="flex items-start gap-3 text-blue-50">
                <span className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-md bg-white/10">
                  <Icon className="size-4" aria-hidden="true" />
                </span>
                <span className="text-base leading-snug">{text}</span>
              </li>
            ))}
          </ul>
        </div>
        <p className="relative text-sm text-blue-200">
          Request · Design · Production · Delivery and Installation · Turnover
        </p>
      </aside>

      <main className="flex flex-col items-center justify-center px-4 py-10 sm:px-8">
        <div className="w-full max-w-sm">
          <AppLogo size="lg" className="mb-8 lg:hidden" />
          <Outlet />
        </div>
      </main>
    </div>
  );
}
