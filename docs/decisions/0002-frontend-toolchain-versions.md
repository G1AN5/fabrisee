# 0002 — Frontend toolchain versions and shadcn/ui primitives

Date: 2026-11-11 · Status: accepted

## Context

The build guide asks for the current stable versions of React, TypeScript, Vite, Tailwind CSS
and shadcn/ui. Three things did not fit together on the day the project was set up.

## Decisions

1. **TypeScript 6.0, not 7.0.** `typescript-eslint` 8.72 supports TypeScript below 6.1 only.
   TypeScript is pinned to `~6.0.3` until typescript-eslint supports 7; then raise the pin.
2. **shadcn/ui primitives are written by hand** in `frontend/src/components/ui/`. The shadcn
   registry (`ui.shadcn.com`) is not reachable from Claude Code cloud sessions, so the CLI
   could not copy the components. The files follow the shadcn conventions (Radix primitives
   from the `radix-ui` package, `cn()` in `src/lib/utils.ts`, `data-slot` attributes, CSS
   variables in `src/styles/globals.css`), and `components.json` is present, so
   `npx shadcn@latest add <component>` works from a network that can reach the registry
   (for example a codespace). Restyle anything added that way with the FabriSee tokens.
3. **No `eslint-plugin-jsx-a11y` yet.** It does not support ESLint 10. Accessibility is checked
   by hand against the checklist in the guide (section 11.8) until the plugin catches up or
   an automated check (for example axe in Playwright) is added in Milestone 9.
4. **Node 22** in the dev container and CI (the version the app was built and tested with).
   React Router 8 needs Node 22.22 or newer.

## Consequences

- `npm run lint`, `npm run typecheck`, `npm test` and `npm run build` pass without peer
  dependency overrides.
- The focus ring, control heights and type scale are defined once in `globals.css`; the
  primitives do not carry their own focus styles.
