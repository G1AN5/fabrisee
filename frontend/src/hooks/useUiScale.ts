import { useLayoutEffect } from "react";

/**
 * Tells the style sheet which area is on screen. The client portal reads one type step
 * larger than the staff workspace (16 px instead of 14 px) and has taller controls; see
 * `html[data-ui="portal"]` in styles/globals.css. The attribute is set on <html> so it
 * also covers dialogs and menus, which render outside the layout.
 */
export function useUiScale(area: "staff" | "portal" | "auth") {
  useLayoutEffect(() => {
    const root = document.documentElement;
    root.dataset.ui = area;
    return () => {
      delete root.dataset.ui;
    };
  }, [area]);
}
