import js from "@eslint/js";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import globals from "globals";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist", "coverage", "playwright-report", "test-results"] },
  {
    files: ["**/*.{ts,tsx}"],
    extends: [
      js.configs.recommended,
      ...tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2022,
      globals: globals.browser,
    },
    rules: {
      // Strict TypeScript: `any` needs an eslint-disable comment that explains why.
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/consistent-type-imports": ["error", { fixStyle: "inline-type-imports" }],
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
      "no-console": ["warn", { allow: ["warn", "error"] }],
    },
  },
  {
    // shadcn/ui primitives export variant helpers next to components; route and context
    // modules export hooks and objects next to components.
    files: ["src/components/ui/**", "src/lib/**", "src/router.tsx"],
    rules: { "react-refresh/only-export-components": "off" },
  },
  {
    files: ["e2e/**", "*.config.{ts,js}"],
    languageOptions: { globals: globals.node },
    rules: { "react-hooks/rules-of-hooks": "off" },
  },
);
