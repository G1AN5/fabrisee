import { Tabs as TabsPrimitive } from "radix-ui";
import type * as React from "react";
import { useEffect, useRef } from "react";

import { cn } from "@/lib/utils";

function Tabs({ className, ...props }: React.ComponentProps<typeof TabsPrimitive.Root>) {
  return (
    <TabsPrimitive.Root data-slot="tabs" className={cn("flex flex-col", className)} {...props} />
  );
}

/** Underlined tabs. The list scrolls sideways on narrow screens; the page never does. */
function TabsList({ className, ...props }: React.ComponentProps<typeof TabsPrimitive.List>) {
  const listRef = useRef<HTMLDivElement>(null);

  // On a phone the selected tab can be outside the visible part of the list: bring it into view.
  // Only the list scrolls sideways (scrollIntoView could also move the page).
  useEffect(() => {
    const list = listRef.current;
    if (!list) return;
    const reveal = () => {
      const active = list.querySelector<HTMLElement>('[data-state="active"]');
      if (!active) return;
      const left = active.offsetLeft;
      const right = left + active.offsetWidth;
      if (left < list.scrollLeft) list.scrollLeft = left;
      else if (right > list.scrollLeft + list.clientWidth) {
        list.scrollLeft = right - list.clientWidth;
      }
    };
    reveal();
    const observer = new MutationObserver(reveal);
    observer.observe(list, { attributes: true, attributeFilter: ["data-state"], subtree: true });
    return () => observer.disconnect();
  }, []);

  return (
    <TabsPrimitive.List
      ref={listRef}
      data-slot="tabs-list"
      className={cn(
        "relative flex gap-1 overflow-x-auto border-b [scrollbar-width:none] sm:gap-2 [&::-webkit-scrollbar]:hidden",
        className,
      )}
      {...props}
    />
  );
}

function TabsTrigger({ className, ...props }: React.ComponentProps<typeof TabsPrimitive.Trigger>) {
  return (
    <TabsPrimitive.Trigger
      data-slot="tabs-trigger"
      className={cn(
        "relative -mb-px inline-flex min-h-11 shrink-0 items-center gap-2 border-b-2 border-transparent px-3 text-sm font-medium whitespace-nowrap text-muted-foreground",
        "transition-colors duration-150 ease-out -outline-offset-2 hover:text-foreground",
        "data-[state=active]:border-primary data-[state=active]:text-primary",
        className,
      )}
      {...props}
    />
  );
}

function TabsContent({ className, ...props }: React.ComponentProps<typeof TabsPrimitive.Content>) {
  return (
    <TabsPrimitive.Content
      data-slot="tabs-content"
      className={cn("pt-5 outline-offset-4", className)}
      {...props}
    />
  );
}

export { Tabs, TabsContent, TabsList, TabsTrigger };
