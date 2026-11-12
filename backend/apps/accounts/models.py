from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Role(models.TextChoices):
    CLIENT = "client", "Client"
    ADMIN = "admin", "Administrator"
    PROJECT_MANAGER = "project_manager", "Project manager"
    DESIGNER = "designer", "Designer"
    PRODUCTION = "production", "Production staff"


STAFF_ROLES = (Role.ADMIN, Role.PROJECT_MANAGER, Role.DESIGNER, Role.PRODUCTION)


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        user = self.model(email=self.normalize_email(email).lower(), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", Role.ADMIN)
        if extra_fields["is_staff"] is not True or extra_fields["is_superuser"] is not True:
            raise ValueError("A superuser must have is_staff=True and is_superuser=True.")
        return self._create_user(email, password, **extra_fields)

    def get_by_natural_key(self, email):
        return self.get(email__iexact=email)


class User(AbstractUser):
    """A person who signs in to FabriSee: a client user or a staff member.

    The email address is the login. `role` decides what the user may do (build guide,
    section 7). `is_staff` and `is_superuser` only control access to the Django admin site.
    """

    username = None
    first_name = None
    last_name = None
    date_joined = None

    email = models.EmailField("email address", unique=True)
    full_name = models.CharField(max_length=150)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CLIENT)
    # Required if and only if the role is `client`.
    client = models.ForeignKey(
        "clients.Client",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="users",
    )
    phone = models.CharField(max_length=30, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    # Data Privacy Act notice acknowledged at first sign-in (build guide, section 16).
    privacy_acknowledged_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    objects = UserManager()

    class Meta:
        ordering = ["full_name"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    (Q(role=Role.CLIENT) & Q(client__isnull=False))
                    | (~Q(role=Role.CLIENT) & Q(client__isnull=True))
                ),
                name="user_client_iff_client_role",
                violation_error_message=(
                    "Client users must belong to a client; staff members must not."
                ),
            ),
        ]

    def __str__(self):
        return f"{self.full_name} <{self.email}>"

    def clean(self):
        super().clean()
        self.email = (self.email or "").strip().lower()
        if self.role == Role.CLIENT and self.client_id is None:
            raise ValidationError({"client": "Choose the client this user belongs to."})
        if self.role != Role.CLIENT and self.client_id is not None:
            raise ValidationError({"client": "Only users with the client role belong to a client."})

    def save(self, *args, **kwargs):
        self.email = (self.email or "").strip().lower()
        super().save(*args, **kwargs)

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return self.short_name

    @property
    def is_client_user(self) -> bool:
        return self.role == Role.CLIENT

    @property
    def is_company_staff(self) -> bool:
        """True for the four staff roles (not to be confused with Django's `is_staff`)."""
        return self.role in STAFF_ROLES

    @property
    def short_name(self) -> str:
        """`A. Villanueva` for `Andrea Villanueva` (used in labels and activity text)."""
        parts = self.full_name.split()
        if len(parts) < 2:
            return self.full_name
        return f"{parts[0][0]}. {' '.join(parts[1:])}"

    @property
    def initials(self) -> str:
        parts = self.full_name.split()
        if not parts:
            return "?"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return (parts[0][0] + parts[-1][0]).upper()

    @property
    def home_path(self) -> str:
        """Where the React app sends the user after sign-in."""
        return "/portal" if self.is_client_user else "/app"
