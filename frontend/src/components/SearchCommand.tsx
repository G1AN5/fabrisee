import { FolderKanban, LoaderCircle, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router";

import { ProjectNumber } from "@/components/ProjectNumber";
import { StageChip } from "@/components/StageChip";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { useProjects } from "@/features/projects/api";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { projectPath, useCurrentUser } from "@/lib/auth";
import { cn } from "@/lib/utils";

/** True on Apple devices, where the shortcut is ⌘K instead of Ctrl+K. */
function isApple(): boolean {
  return /Mac|iPhone|iPad/.test(navigator.platform);
}

interface SearchCommandProps {
  className?: string;
}

/**
 * Global search: find a project by number, title, or client and jump to it.
 * Opens with the button or with Ctrl+K (⌘K on a Mac).
 */
export function SearchCommand({ className }: SearchCommandProps) {
  const user = useCurrentUser();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [text, setText] = useState("");
  const query = useDebouncedValue(text.trim(), 200);
  const results = useProjects({ q: query, page_size: 8 }, { enabled: open && query.length > 0 });
  const shortcut = isApple() ? "⌘K" : "Ctrl K";

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key.toLowerCase() === "k" && (event.metaKey || event.ctrlKey)) {
        event.preventDefault();
        setOpen((value) => !value);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  function close() {
    setOpen(false);
    setText("");
  }

  const searching = query.length > 0 && (results.isFetching || query !== text.trim());
  const projects = query.length > 0 ? (results.data?.results ?? []) : [];

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className={cn(
          "flex h-(--control-h) min-w-0 items-center gap-2 rounded-md border border-input bg-card px-3 text-sm text-muted-foreground shadow-xs transition-colors duration-150 ease-out hover:bg-accent",
          className,
        )}
      >
        <Search className="size-4 shrink-0" aria-hidden="true" />
        <span className="min-w-0 flex-1 truncate text-left">Search projects</span>
        <kbd
          aria-hidden="true"
          className="hidden shrink-0 rounded-sm border bg-muted px-1.5 py-0.5 text-[0.6875rem] font-medium text-muted-foreground sm:inline-block"
        >
          {shortcut}
        </kbd>
      </button>

      <CommandDialog
        open={open}
        onOpenChange={(next) => (next ? setOpen(true) : close())}
        title="Search projects"
        description="Search by project number, title, or client."
        shouldFilter={false}
      >
        <CommandInput
          value={text}
          onValueChange={setText}
          placeholder="Project number, title, or client"
          aria-label="Search projects"
        />
        <CommandList>
          {query.length === 0 && (
            <p className="px-4 py-8 text-center text-sm text-muted-foreground">
              Type a project number, a title, or a client name.
            </p>
          )}
          {searching && projects.length === 0 && (
            <p className="flex items-center justify-center gap-2 px-4 py-8 text-sm text-muted-foreground">
              <LoaderCircle className="size-4 animate-spin" aria-hidden="true" />
              Searching
            </p>
          )}
          {results.isError && query.length > 0 && (
            <p role="alert" className="px-4 py-8 text-center text-sm text-muted-foreground">
              The search could not be completed. Try again.
            </p>
          )}
          {query.length > 0 && !searching && !results.isError && (
            <CommandEmpty>No project matches “{query}”.</CommandEmpty>
          )}
          {projects.length > 0 && (
            <CommandGroup heading="Projects">
              {projects.map((project) => (
                <CommandItem
                  key={project.id}
                  value={String(project.id)}
                  onSelect={() => {
                    close();
                    navigate(projectPath(user, project.id));
                  }}
                >
                  <FolderKanban
                    className="size-4 shrink-0 text-muted-foreground"
                    aria-hidden="true"
                  />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate font-medium text-foreground">
                      {project.title}
                    </span>
                    <span className="flex gap-2 text-xs text-muted-foreground">
                      <ProjectNumber value={project.project_number} />
                      <span className="truncate">{project.client.company_name}</span>
                    </span>
                  </span>
                  <StageChip stage={project.stage} short />
                </CommandItem>
              ))}
            </CommandGroup>
          )}
        </CommandList>
      </CommandDialog>
    </>
  );
}
