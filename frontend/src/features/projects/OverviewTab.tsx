import { Mail, Phone, UserRoundCheck } from "lucide-react";
import type { ReactNode } from "react";

import { EmptyState } from "@/components/EmptyState";
import { Avatar } from "@/components/ui/avatar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { describeDue, formatDate, formatDateTime } from "@/lib/format";
import type { Contact, ProjectDetail } from "@/lib/types";
import { cn } from "@/lib/utils";

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <dt className="text-xs font-medium text-muted-foreground">{label}</dt>
      <dd className="mt-0.5 text-foreground">{children}</dd>
    </div>
  );
}

function Person({ person, note }: { person: Contact; note?: string }) {
  return (
    <li className="flex items-start gap-3">
      <Avatar initials={person.initials} className="mt-0.5" />
      <div className="min-w-0">
        <p className="truncate font-medium text-foreground">{person.full_name}</p>
        <p className="truncate text-xs text-muted-foreground">
          {note ?? (person.job_title || person.role_label)}
        </p>
        <p className="mt-1 flex flex-col gap-0.5 text-xs">
          {person.email && (
            <a
              href={`mailto:${person.email}`}
              className="inline-flex items-center gap-1.5 truncate rounded-sm text-link underline-offset-2 hover:underline"
            >
              <Mail className="size-3.5 shrink-0" aria-hidden="true" />
              <span className="truncate">{person.email}</span>
            </a>
          )}
          {person.phone && (
            <a
              href={`tel:${person.phone.replace(/\s+/g, "")}`}
              className="inline-flex items-center gap-1.5 rounded-sm text-link underline-offset-2 hover:underline"
            >
              <Phone className="size-3.5 shrink-0" aria-hidden="true" />
              {person.phone}
            </a>
          )}
        </p>
      </div>
    </li>
  );
}

interface OverviewTabProps {
  project: ProjectDetail;
  /** The client portal: no client record, and "your" wording. */
  forClient?: boolean;
}

/** The details of a project, the people on it, and the designated approvers. */
export function OverviewTab({ project, forClient = false }: OverviewTabProps) {
  const open = project.status === "active" || project.status === "on_hold";
  const client = project.client;

  return (
    <div className="grid items-start gap-6 lg:grid-cols-3">
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Project details</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid gap-x-8 gap-y-5 sm:grid-cols-2">
            <Field label="Project type">{project.project_type_label}</Field>
            <Field label="Target date">
              <span className="tabular-nums">{formatDate(project.target_date)}</span>
              {open && (
                <span
                  className={cn(
                    "ml-2 text-xs",
                    project.is_overdue ? "font-medium text-destructive" : "text-muted-foreground",
                  )}
                >
                  {describeDue(project.days_until_target)}
                </span>
              )}
            </Field>
            <Field label="Location">{project.location}</Field>
            <Field label="Dimensions">{project.dimensions}</Field>
            <div className="sm:col-span-2">
              <Field label="Description">
                {project.description ? (
                  <span className="whitespace-pre-line">{project.description}</span>
                ) : (
                  <span className="text-muted-foreground">No description</span>
                )}
              </Field>
            </div>
            <Field label="Request submitted">
              <span className="tabular-nums">{formatDateTime(project.created_at)}</span>
              {project.created_by && (
                <span className="text-muted-foreground"> by {project.created_by.full_name}</span>
              )}
            </Field>
          </dl>
        </CardContent>
      </Card>

      <div className="flex flex-col gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Designated approvers</CardTitle>
          </CardHeader>
          {project.approvers.length === 0 ? (
            <EmptyState
              compact
              icon={UserRoundCheck}
              title="No designated approvers yet"
              description={
                forClient
                  ? "Your project manager sets who decides on quotations and designs."
                  : "The project manager designates who decides on quotations and designs before a quotation is sent."
              }
            />
          ) : (
            <CardContent>
              <p className="mb-4 text-xs text-muted-foreground">
                {project.approvers.length === 1
                  ? "This person decides on quotations and approves design revisions."
                  : "Any one of them decides on a quotation. All of them must approve a design revision."}
              </p>
              <ul className="flex flex-col gap-4">
                {project.approvers.map((person) => (
                  <Person key={person.id} person={person} />
                ))}
              </ul>
            </CardContent>
          )}
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{forClient ? "Your project manager" : "Team"}</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="flex flex-col gap-4">
              {project.manager ? (
                <Person person={project.manager} note="Project manager" />
              ) : (
                <li className="text-muted-foreground">No project manager is assigned yet.</li>
              )}
              {!forClient && project.designer && (
                <li className="flex items-start gap-3">
                  <Avatar initials={project.designer.initials} className="mt-0.5" />
                  <div className="min-w-0">
                    <p className="truncate font-medium text-foreground">
                      {project.designer.full_name}
                    </p>
                    <p className="text-xs text-muted-foreground">Designer</p>
                  </div>
                </li>
              )}
            </ul>
          </CardContent>
        </Card>

        {!forClient && (
          <Card>
            <CardHeader>
              <CardTitle>Client</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="flex flex-col gap-3">
                <Field label="Company">{client.company_name}</Field>
                {client.contact_person && (
                  <Field label="Contact person">{client.contact_person}</Field>
                )}
                {client.email && (
                  <Field label="Email">
                    <a
                      href={`mailto:${client.email}`}
                      className="rounded-sm text-link underline-offset-2 hover:underline"
                    >
                      {client.email}
                    </a>
                  </Field>
                )}
                {client.phone && <Field label="Phone">{client.phone}</Field>}
                {client.address && <Field label="Address">{client.address}</Field>}
                {client.notes && (
                  <Field label="Notes (staff only)">
                    <span className="whitespace-pre-line">{client.notes}</span>
                  </Field>
                )}
              </dl>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
