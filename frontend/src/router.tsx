import { createBrowserRouter } from "react-router";

import { FoundationPage } from "@/features/dev/FoundationPage";

export const router = createBrowserRouter([{ path: "*", element: <FoundationPage /> }]);
