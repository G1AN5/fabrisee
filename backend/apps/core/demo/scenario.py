"""Tools for writing the history of a demo project in chronological order.

The process rules (PR1 to PR8) are implemented as services from Milestone 3 on. Until then
the demo data writes the records of each step directly, with past dates, in the same shape
the services will produce: stage updates, activity entries, notifications, and emails.

TODO(M3 to M7): replace the direct writes with calls to the services as they arrive, so
the demo data always follows the rules.
"""

import io
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.core.files.base import ContentFile
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.activity.models import ActivityAction
from apps.activity.services import log_activity
from apps.core.choices import DecisionChannel
from apps.core.files import make_thumbnail
from apps.core.models import SystemSetting
from apps.designs.models import Approval, ApprovalDecision, DesignRevision, RevisionStatus
from apps.notifications import messages
from apps.notifications.models import EmailLog, EmailStatus, Notification, NotificationEvent
from apps.notifications.services import email_subject, render_email_text
from apps.projects.links import project_path
from apps.projects.models import (
    Document,
    DocumentType,
    Project,
    ProjectApprover,
    ProjectStatus,
    Stage,
    StageUpdate,
    StageUpdateSource,
)
from apps.projects.numbering import next_project_number
from apps.projects.selectors import ProjectState, pending_decisions_of, with_related
from apps.quotations.models import Quotation, QuotationStatus

from . import drawing, pdfs

# Notifications older than this are shown as already read.
READ_AFTER = timedelta(days=3, hours=12)


class DemoBuilder:
    """Shared state of one seed run: the clock, the people, and the companies."""

    def __init__(self, now: datetime):
        self.now = now
        self.today: date = timezone.localtime(now).date()
        self.company = SystemSetting.load().company_name
        self.reminder_threshold = timedelta(hours=SystemSetting.load().reminder_hours)
        self.users: dict[str, User] = {}
        self.clients: dict = {}

    # --- time ------------------------------------------------------------------------

    def on(self, days_ago: int, clock: str) -> datetime:
        """`clock` (Manila time) on the day `days_ago` days before today."""
        if days_ago < 1:
            raise ValueError("Use hours_ago() for events of today.")
        hour, minute = (int(part) for part in clock.split(":"))
        local_now = timezone.localtime(self.now)
        return local_now.replace(hour=hour, minute=minute, second=0, microsecond=0) - timedelta(
            days=days_ago
        )

    def at_least(self, days: int, clock: str) -> datetime:
        """The latest moment at `clock` that is at least `days` full days before now."""
        moment = self.on(days, clock)
        if self.now - moment < timedelta(days=days):
            moment -= timedelta(days=1)
        return moment

    def hours_ago(self, hours: float) -> datetime:
        return self.now - timedelta(hours=hours)

    def date_in(self, days: int) -> date:
        return self.today + timedelta(days=days)

    # --- people ------------------------------------------------------------------------

    def user(self, key: str) -> User:
        return self.users[key]

    def staff_with_role(self, role: str) -> list[User]:
        return [user for user in self.users.values() if user.role == role and user.is_active]

    # --- notifications -----------------------------------------------------------------

    def notify(
        self,
        *,
        event: str,
        recipients,
        message: messages.Message,
        project: Project,
        section: str,
        at: datetime,
        actor: User | None = None,
    ) -> None:
        """Write a past notification and its email, like `notifications.services.notify`."""
        seen: set[int] = set()
        for user in recipients:
            if user is None or user.pk in seen:
                continue
            seen.add(user.pk)
            if not user.is_active or (actor is not None and user.pk == actor.pk):
                continue
            link = project_path(user, project, section)
            notification = Notification.objects.create(
                user=user,
                project=project,
                event=event,
                title=message.title,
                message=message.body,
                link=link,
                created_at=at,
            )
            EmailLog.objects.create(
                to=user.email,
                subject=email_subject(message.title, project),
                body_text=render_email_text(
                    user=user, title=message.title, message=message.body, link=link, project=project
                ),
                notification=notification,
                status=EmailStatus.LOGGED,
                created_at=at,
            )

    def finalize_read_state(self) -> None:
        """Older notifications are read; every demo user keeps at least one unread."""
        cutoff = self.now - READ_AFTER
        for notification in Notification.objects.filter(created_at__lt=cutoff):
            notification.is_read = True
            notification.read_at = min(self.now, notification.created_at + timedelta(hours=3))
            notification.save(update_fields=["is_read", "read_at"])
        for user in self.users.values():
            own = Notification.objects.filter(user=user)
            if own.exists() and not own.filter(is_read=False).exists():
                latest = own.order_by("-created_at", "-id").first()
                latest.is_read = False
                latest.read_at = None
                latest.save(update_fields=["is_read", "read_at"])


class ProjectStory:
    """The history of one demo project. Call the steps in chronological order."""

    def __init__(
        self,
        builder: DemoBuilder,
        *,
        client_key: str,
        title: str,
        project_type: str,
        location: str,
        dimensions: str,
        description: str,
        target_date: date,
        manager_key: str,
        scene: str,
        designer_key: str | None = "designer",
    ):
        self.b = builder
        self.client = builder.clients[client_key]
        self.title = title
        self.project_type = project_type
        self.location = location
        self.dimensions = dimensions
        self.description = description
        self.target_date = target_date
        self.manager = builder.user(manager_key)
        self.designer = builder.user(designer_key) if designer_key else None
        self.scene = scene
        self.project: Project | None = None
        self.last_at: datetime | None = None

    # --- internals -----------------------------------------------------------------

    def _step(self, at: datetime) -> datetime:
        """Check that steps are written in order and never in the future."""
        if at > self.b.now:
            raise ValueError(f"{self.title}: step at {at} is in the future")
        if self.last_at is not None and at < self.last_at:
            raise ValueError(f"{self.title}: step at {at} is before the previous step")
        self.last_at = at
        return at

    @property
    def client_users(self) -> list[User]:
        return [u for u in self.b.users.values() if u.client_id == self.client.pk and u.is_active]

    @property
    def approvers(self) -> list[User]:
        links = ProjectApprover.objects.filter(project=self.project).select_related("user")
        return [link.user for link in links.order_by("id")]

    def _subtitle(self) -> str:
        return f"{self.client.company_name} · {self.project.project_number}"

    def _local_date(self, at: datetime) -> date:
        return timezone.localtime(at).date()

    def _change_stage(self, *, to_stage, by, at, source, remarks="", rule="") -> None:
        project = self.project
        from_stage = project.stage
        project.stage = to_stage
        if to_stage == Stage.TURNOVER:
            project.status = ProjectStatus.COMPLETED
        project.save(update_fields=["stage", "status", "updated_at"])
        StageUpdate.objects.create(
            project=project,
            from_stage=from_stage,
            to_stage=to_stage,
            remarks=remarks,
            updated_by=by,
            source=source,
            created_at=at,
        )
        details = {"from_stage": from_stage, "to_stage": to_stage, "source": source}
        if rule:
            details["rule"] = rule
        log_activity(
            action=ActivityAction.STAGE_CHANGED, actor=by, project=project, details=details, at=at
        )

    # --- steps -------------------------------------------------------------------------

    def submit(self, by_key: str, at: datetime, references=()) -> "ProjectStory":
        """PR2: the client submits the request; the project starts in Request."""
        self._step(at)
        by = self.b.user(by_key)
        self.project = Project.objects.create(
            project_number=next_project_number(at),
            client=self.client,
            title=self.title,
            project_type=self.project_type,
            location=self.location,
            target_date=self.target_date,
            dimensions=self.dimensions,
            description=self.description,
            manager=self.manager,
            created_by=by,
            created_at=at,
        )
        StageUpdate.objects.create(
            project=self.project,
            from_stage="",
            to_stage=Stage.REQUEST,
            remarks="Request received.",
            updated_by=by,
            source=StageUpdateSource.RULE,
            created_at=at,
        )
        log_activity(action=ActivityAction.REQUEST_SUBMITTED, actor=by, project=self.project, at=at)
        for name, content in references:
            self.add_document(
                by_key,
                at,
                doc_type=DocumentType.REFERENCE,
                name=name,
                content=content,
                visible=True,
            )
        self.b.notify(
            event=NotificationEvent.REQUEST_SUBMITTED,
            recipients=[self.manager],
            message=messages.request_submitted(self.project, by),
            project=self.project,
            section="overview",
            at=at,
            actor=by,
        )
        return self

    def designate(self, by_key: str, at: datetime, approver_keys: list[str]) -> "ProjectStory":
        self._step(at)
        by = self.b.user(by_key)
        users = [self.b.user(key) for key in approver_keys]
        for user in users:
            ProjectApprover.objects.create(project=self.project, user=user, created_at=at)
        log_activity(
            action=ActivityAction.APPROVERS_CHANGED,
            actor=by,
            project=self.project,
            details={"approvers": [user.full_name for user in users]},
            at=at,
        )
        return self

    def quote(
        self,
        by_key: str,
        at: datetime,
        items: list[tuple[str, int, int]],
        *,
        notes: str = "",
        send: bool = True,
    ) -> "ProjectStory":
        """PR3: a new quotation version (upload and send, or save as a draft)."""
        self._step(at)
        by = self.b.user(by_key)
        project = self.project
        Quotation.objects.filter(
            project=project,
            status__in=[QuotationStatus.DRAFT, QuotationStatus.SENT, QuotationStatus.RETURNED],
        ).update(status=QuotationStatus.SUPERSEDED)
        version_no = Quotation.objects.filter(project=project).count() + 1
        priced = [(text, quantity, Decimal(price)) for text, quantity, price in items]
        amount = sum((price * quantity for _, quantity, price in priced), Decimal("0"))
        contact = self.client_users[0] if self.client_users else None
        pdf = pdfs.quotation_pdf(
            company=self.b.company,
            project_number=project.project_number,
            project_title=project.title,
            location=project.location,
            client_name=self.client.company_name,
            contact_name=self.client.contact_person or (contact.full_name if contact else ""),
            client_address=self.client.address,
            version_no=version_no,
            issued_on=self._local_date(at),
            target_date=project.target_date,
            prepared_by=f"{by.full_name}, {by.job_title}",
            items=priced,
            notes=notes,
        )
        quotation = Quotation(
            project=project,
            version_no=version_no,
            amount=amount,
            notes=notes,
            status=QuotationStatus.SENT if send else QuotationStatus.DRAFT,
            prepared_by=by,
            sent_at=at if send else None,
            created_at=at,
        )
        quotation.file.save(f"quotation-v{version_no}.pdf", ContentFile(pdf), save=False)
        quotation.save()
        log_activity(
            action=ActivityAction.QUOTATION_CREATED,
            actor=by,
            project=project,
            details={"version_no": version_no},
            at=at,
        )
        if send:
            log_activity(
                action=ActivityAction.QUOTATION_SENT,
                actor=by,
                project=project,
                details={"version_no": version_no},
                at=at,
            )
            approvers = self.approvers
            self.b.notify(
                event=NotificationEvent.QUOTATION_SENT,
                recipients=approvers,
                message=messages.quotation_sent(quotation, decision_needed=True),
                project=project,
                section="quotation",
                at=at,
                actor=by,
            )
            others = [user for user in self.client_users if user not in approvers]
            self.b.notify(
                event=NotificationEvent.QUOTATION_SENT,
                recipients=others,
                message=messages.quotation_sent(quotation, decision_needed=False),
                project=project,
                section="quotation",
                at=at,
                actor=by,
            )
        return self

    def _sent_quotation(self) -> Quotation:
        return Quotation.objects.get(project=self.project, status=QuotationStatus.SENT)

    def accept_quotation(
        self,
        by_key: str,
        at: datetime,
        *,
        recorder_key: str | None = None,
        channel: str = DecisionChannel.PORTAL,
    ) -> "ProjectStory":
        """PR3: a designated approver accepts; the project moves to Design."""
        self._step(at)
        approver = self.b.user(by_key)
        recorder = self.b.user(recorder_key) if recorder_key else None
        actor = recorder or approver
        quotation = self._sent_quotation()
        quotation.status = QuotationStatus.ACCEPTED
        quotation.decided_by = approver
        quotation.decided_at = at
        quotation.decided_on_behalf = recorder is not None
        quotation.decision_channel = channel
        quotation.recorded_by = recorder
        quotation.save()
        log_activity(
            action=ActivityAction.QUOTATION_ACCEPTED,
            actor=actor,
            project=self.project,
            details={
                "version_no": quotation.version_no,
                "on_behalf": recorder is not None,
                "approver_name": approver.short_name,
                "channel": channel,
            },
            at=at,
        )
        if self.designer is not None:
            self.project.designer = self.designer
            self.project.save(update_fields=["designer", "updated_at"])
        self._change_stage(
            to_stage=Stage.DESIGN,
            by=actor,
            at=at,
            source=StageUpdateSource.RULE,
            remarks=f"Quotation {quotation.label} accepted.",
            rule="PR3",
        )
        self.b.notify(
            event=NotificationEvent.QUOTATION_DECIDED,
            recipients=[self.manager, self.designer],
            message=messages.quotation_decided(quotation, accepted=True, decided_by=approver),
            project=self.project,
            section="quotation",
            at=at,
            actor=actor,
        )
        return self

    def return_quotation(self, by_key: str, at: datetime, comment: str) -> "ProjectStory":
        """PR3: a designated approver returns the quotation; a new version is needed."""
        self._step(at)
        approver = self.b.user(by_key)
        quotation = self._sent_quotation()
        quotation.status = QuotationStatus.RETURNED
        quotation.decided_by = approver
        quotation.decided_at = at
        quotation.client_comment = comment
        quotation.decision_channel = DecisionChannel.PORTAL
        quotation.save()
        log_activity(
            action=ActivityAction.QUOTATION_RETURNED,
            actor=approver,
            project=self.project,
            details={"version_no": quotation.version_no},
            at=at,
        )
        self.b.notify(
            event=NotificationEvent.QUOTATION_DECIDED,
            recipients=[self.manager],
            message=messages.quotation_decided(quotation, accepted=False, decided_by=approver),
            project=self.project,
            section="quotation",
            at=at,
            actor=approver,
        )
        return self

    def upload_revision(
        self,
        by_key: str,
        at: datetime,
        *,
        notes: str,
        materials: list[tuple[str, str, str]],
        **scene_options,
    ) -> "ProjectStory":
        """PR4: the next numbered design revision, with render and spec sheet."""
        self._step(at)
        by = self.b.user(by_key)
        project = self.project
        for pending in DesignRevision.objects.filter(
            project=project, status=RevisionStatus.PENDING_APPROVAL
        ):
            pending.status = RevisionStatus.SUPERSEDED
            pending.save()
            log_activity(
                action=ActivityAction.REVISION_SUPERSEDED,
                actor=by,
                project=project,
                details={"revision_no": pending.revision_no},
                at=at,
            )
        revision_no = DesignRevision.objects.filter(project=project).count() + 1
        label = f"R{revision_no}"
        issued = self._local_date(at)
        render = drawing.render_image(
            self.scene,
            title=project.title,
            subtitle=self._subtitle(),
            label=f"{label} · {pdfs.long_date(issued)}",
            **scene_options,
        )
        spec = pdfs.spec_sheet_pdf(
            company=self.b.company,
            project_number=project.project_number,
            project_title=project.title,
            client_name=self.client.company_name,
            revision_label=label,
            issued_on=issued,
            designer=by.full_name,
            dimensions=project.dimensions,
            materials=materials,
            notes=notes,
        )
        revision = DesignRevision(
            project=project,
            revision_no=revision_no,
            notes=notes,
            status=RevisionStatus.PENDING_APPROVAL,
            uploaded_by=by,
            uploaded_at=at,
            created_at=at,
        )
        revision.render.save(f"render-r{revision_no}.png", ContentFile(render), save=False)
        revision.spec_sheet.save(f"spec-r{revision_no}.pdf", ContentFile(spec), save=False)
        thumbnail = make_thumbnail(io_bytes(render))
        if thumbnail is not None:
            revision.thumbnail.save("thumbnail.webp", thumbnail, save=False)
        revision.save()
        log_activity(
            action=ActivityAction.REVISION_UPLOADED,
            actor=by,
            project=project,
            details={"revision_no": revision_no},
            at=at,
        )
        self.b.notify(
            event=NotificationEvent.REVISION_UPLOADED,
            recipients=self.approvers,
            message=messages.revision_uploaded(revision, decision_needed=True),
            project=project,
            section="design",
            at=at,
            actor=by,
        )
        self.b.notify(
            event=NotificationEvent.REVISION_UPLOADED,
            recipients=[self.manager],
            message=messages.revision_uploaded(revision, decision_needed=False),
            project=project,
            section="design",
            at=at,
            actor=by,
        )
        return self

    def _pending_revision(self) -> DesignRevision:
        return DesignRevision.objects.get(
            project=self.project, status=RevisionStatus.PENDING_APPROVAL
        )

    def approve(
        self,
        by_key: str,
        at: datetime,
        *,
        comment: str = "",
        recorder_key: str | None = None,
        channel: str = DecisionChannel.PORTAL,
    ) -> "ProjectStory":
        """PR5: one approver approves; when all have, the revision is locked."""
        self._step(at)
        approver = self.b.user(by_key)
        recorder = self.b.user(recorder_key) if recorder_key else None
        actor = recorder or approver
        revision = self._pending_revision()
        Approval.objects.create(
            revision=revision,
            approver=approver,
            decision=ApprovalDecision.APPROVED,
            comment=comment,
            decided_on_behalf=recorder is not None,
            decision_channel=channel,
            recorded_by=recorder,
            created_at=at,
        )
        log_activity(
            action=ActivityAction.REVISION_APPROVED_BY,
            actor=actor,
            project=self.project,
            details={
                "revision_no": revision.revision_no,
                "on_behalf": recorder is not None,
                "approver_name": approver.short_name,
                "channel": channel,
            },
            at=at,
        )
        approved_ids = set(
            revision.approvals.filter(decision=ApprovalDecision.APPROVED).values_list(
                "approver_id", flat=True
            )
        )
        if all(user.pk in approved_ids for user in self.approvers):
            revision.status = RevisionStatus.APPROVED
            revision.locked_at = at
            revision.save()
            log_activity(
                action=ActivityAction.REVISION_LOCKED,
                project=self.project,
                details={"revision_no": revision.revision_no},
                at=at,
            )
            self._change_stage(
                to_stage=Stage.PRODUCTION,
                by=actor,
                at=at,
                source=StageUpdateSource.RULE,
                remarks=f"Design {revision.label} approved by all designated approvers.",
                rule="PR5",
            )
            staff = [self.designer, self.manager, *self.b.staff_with_role(Role.PRODUCTION)]
            self.b.notify(
                event=NotificationEvent.REVISION_APPROVED,
                recipients=staff,
                message=messages.revision_approved(revision, for_client=False),
                project=self.project,
                section="design",
                at=at,
                actor=actor,
            )
            self.b.notify(
                event=NotificationEvent.REVISION_APPROVED,
                recipients=self.client_users,
                message=messages.revision_approved(revision, for_client=True),
                project=self.project,
                section="design",
                at=at,
                actor=actor,
            )
        return self

    def request_changes(self, by_key: str, at: datetime, comment: str) -> "ProjectStory":
        """PR5: an approver requests changes; a new revision is needed."""
        self._step(at)
        approver = self.b.user(by_key)
        revision = self._pending_revision()
        Approval.objects.create(
            revision=revision,
            approver=approver,
            decision=ApprovalDecision.CHANGES_REQUESTED,
            comment=comment,
            created_at=at,
        )
        revision.status = RevisionStatus.CHANGES_REQUESTED
        revision.save()
        log_activity(
            action=ActivityAction.REVISION_CHANGES_REQUESTED_BY,
            actor=approver,
            project=self.project,
            details={"revision_no": revision.revision_no},
            at=at,
        )
        self.b.notify(
            event=NotificationEvent.REVISION_CHANGES_REQUESTED,
            recipients=[self.designer, self.manager],
            message=messages.revision_changes_requested(
                revision, requested_by=approver, comment=comment
            ),
            project=self.project,
            section="design",
            at=at,
            actor=approver,
        )
        return self

    def remind(self, at: datetime) -> "ProjectStory":
        """PR6: remind the pending approvers and alert the manager."""
        self._step(at)
        project = with_related(Project.objects.filter(pk=self.project.pk)).get()
        for decision in pending_decisions_of(
            ProjectState.of(project), at, self.b.reminder_threshold
        ):
            waiting_hours = (at - decision.waiting_since).total_seconds() / 3600
            item = decision.item
            item.last_reminded_at = at
            item.save()
            names = [user.full_name for user in decision.pending_approvers]
            # "quotation v1" or "design R2", as it reads inside a sentence.
            item_text = decision.label[0].lower() + decision.label[1:]
            log_activity(
                action=ActivityAction.REMINDER_SENT,
                project=self.project,
                details={"item": item_text, "recipients": names},
                at=at,
            )
            log_activity(
                action=ActivityAction.OVERDUE_ALERT_SENT,
                project=self.project,
                details={"item": item_text, "recipient": self.manager.full_name},
                at=at,
            )
            section = "quotation" if decision.kind == "quotation" else "design"
            self.b.notify(
                event=NotificationEvent.DECISION_REMINDER,
                recipients=decision.pending_approvers,
                message=messages.decision_reminder(decision.label, waiting_hours=waiting_hours),
                project=self.project,
                section=section,
                at=at,
            )
            self.b.notify(
                event=NotificationEvent.DECISION_OVERDUE_ALERT,
                recipients=[self.manager],
                message=messages.decision_overdue_alert(
                    decision.label, waiting_hours=waiting_hours, pending_names=names
                ),
                project=self.project,
                section=section,
                at=at,
            )
        return self

    def change_stage(
        self, by_key: str, at: datetime, to_stage: str, remarks: str
    ) -> "ProjectStory":
        """PR7: staff record the next stage; the client is notified."""
        self._step(at)
        by = self.b.user(by_key)
        self._change_stage(
            to_stage=to_stage, by=by, at=at, source=StageUpdateSource.MANUAL, remarks=remarks
        )
        if to_stage == Stage.TURNOVER:
            self.b.notify(
                event=NotificationEvent.PROJECT_TURNED_OVER,
                recipients=self.client_users,
                message=messages.project_turned_over(self.project, for_client=True),
                project=self.project,
                section="progress",
                at=at,
                actor=by,
            )
            self.b.notify(
                event=NotificationEvent.PROJECT_TURNED_OVER,
                recipients=[self.manager, *self.b.staff_with_role(Role.ADMIN)],
                message=messages.project_turned_over(self.project, for_client=False),
                project=self.project,
                section="progress",
                at=at,
                actor=by,
            )
        else:
            self.b.notify(
                event=NotificationEvent.STAGE_CHANGED,
                recipients=self.client_users,
                message=messages.stage_changed(self.project, to_stage, for_client=True),
                project=self.project,
                section="progress",
                at=at,
                actor=by,
            )
            self.b.notify(
                event=NotificationEvent.STAGE_CHANGED,
                recipients=[self.manager],
                message=messages.stage_changed(
                    self.project, to_stage, for_client=False, remarks=remarks
                ),
                project=self.project,
                section="progress",
                at=at,
                actor=by,
            )
        return self

    def add_document(
        self,
        by_key: str,
        at: datetime,
        *,
        doc_type: str,
        name: str,
        content: bytes,
        visible: bool,
    ) -> "ProjectStory":
        self._step(at)
        by = self.b.user(by_key)
        is_image = name.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
        document = Document(
            project=self.project,
            doc_type=doc_type,
            original_name=name,
            size_bytes=len(content),
            content_type="image/png" if is_image else "application/pdf",
            visible_to_client=visible,
            uploaded_by=by,
            created_at=at,
        )
        document.file.save(name, ContentFile(content), save=False)
        if is_image:
            thumbnail = make_thumbnail(io_bytes(content))
            if thumbnail is not None:
                document.thumbnail.save("thumbnail.webp", thumbnail, save=False)
        document.save()
        log_activity(
            action=ActivityAction.DOCUMENT_UPLOADED,
            actor=by,
            project=self.project,
            details={
                "document_id": document.pk,
                "name": name,
                "doc_type": doc_type,
                "visible_to_client": visible,
            },
            at=at,
        )
        return self

    def finish(self) -> Project:
        """Set "last updated" to the time of the last step."""
        Project.objects.filter(pk=self.project.pk).update(updated_at=self.last_at)
        self.project.refresh_from_db()
        return self.project


def io_bytes(content: bytes) -> io.BytesIO:
    return io.BytesIO(content)
