import { createBrowserRouter } from "react-router";

import { ComingSoon, NotFoundPage, RouteError } from "@/components/StatusPages";
import { ForgotPasswordPage } from "@/features/auth/ForgotPasswordPage";
import { HomeRedirect, RequireArea, RequirePermission } from "@/features/auth/guards";
import { LoginPage } from "@/features/auth/LoginPage";
import { ApprovalsPage } from "@/features/dashboard/ApprovalsPage";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { PortalHomePage } from "@/features/dashboard/PortalHomePage";
import { NotificationsPage } from "@/features/notifications/NotificationsPage";
import { PortalProjectPage } from "@/features/projects/PortalProjectPage";
import { ProjectDetailPage } from "@/features/projects/ProjectDetailPage";
import { ProjectsListPage } from "@/features/projects/ProjectsListPage";
import { AuthLayout } from "@/layouts/AuthLayout";
import { PortalLayout } from "@/layouts/PortalLayout";
import { StaffLayout } from "@/layouts/StaffLayout";

export const router = createBrowserRouter([
  {
    errorElement: <RouteError />,
    children: [
      { path: "/", element: <HomeRedirect /> },
      {
        element: <AuthLayout />,
        children: [
          { path: "/login", element: <LoginPage /> },
          { path: "/forgot-password", element: <ForgotPasswordPage /> },
        ],
      },
      {
        path: "/app",
        element: (
          <RequireArea area="staff">
            <StaffLayout />
          </RequireArea>
        ),
        children: [
          { index: true, element: <DashboardPage /> },
          { path: "projects", element: <ProjectsListPage /> },
          { path: "projects/:projectId", element: <ProjectDetailPage /> },
          { path: "projects/:projectId/:tab", element: <ProjectDetailPage /> },
          { path: "notifications", element: <NotificationsPage /> },
          {
            path: "approvals",
            element: (
              <RequirePermission permission="view_approvals">
                <ApprovalsPage />
              </RequirePermission>
            ),
          },
          {
            path: "clients",
            element: (
              <RequirePermission permission="view_clients">
                <ComingSoon title="The clients page" milestone="Milestone 3">
                  Client records, their contacts, and their projects will be listed here.
                </ComingSoon>
              </RequirePermission>
            ),
          },
          {
            path: "requests/new",
            element: (
              <RequirePermission permission="submit_request_on_behalf">
                <ComingSoon title="The request form" milestone="Milestone 3">
                  Staff will record a project request on behalf of a client here.
                </ComingSoon>
              </RequirePermission>
            ),
          },
          {
            path: "users",
            element: (
              <RequirePermission permission="manage_users">
                <ComingSoon title="The users page" milestone="Milestone 7">
                  Staff and client users, their roles, and invitations will be managed here.
                </ComingSoon>
              </RequirePermission>
            ),
          },
          {
            path: "settings",
            element: (
              <RequirePermission permission="manage_settings">
                <ComingSoon title="The settings page" milestone="Milestone 7">
                  The company name, project number prefix, reminder threshold, and upload limit will
                  be set here.
                </ComingSoon>
              </RequirePermission>
            ),
          },
          {
            path: "email-outbox",
            element: (
              <RequirePermission permission="view_email_outbox">
                <ComingSoon title="The email outbox" milestone="Milestone 7">
                  Every email FabriSee produces will be listed here.
                </ComingSoon>
              </RequirePermission>
            ),
          },
          { path: "*", element: <NotFoundPage /> },
        ],
      },
      {
        path: "/portal",
        element: (
          <RequireArea area="portal">
            <PortalLayout />
          </RequireArea>
        ),
        children: [
          { index: true, element: <PortalHomePage /> },
          { path: "projects/:projectId", element: <PortalProjectPage /> },
          { path: "projects/:projectId/:tab", element: <PortalProjectPage /> },
          { path: "notifications", element: <NotificationsPage /> },
          {
            path: "requests/new",
            element: (
              <ComingSoon title="The request form" milestone="Milestone 3">
                You will submit a new project request here.
              </ComingSoon>
            ),
          },
          { path: "*", element: <NotFoundPage /> },
        ],
      },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);
