import { createBrowserRouter } from "react-router";
import { Layout } from "./components/Layout";
import { Dashboard } from "./screens/Dashboard";
import { Transactions } from "./screens/Transactions";
import { TransactionDetail } from "./screens/TransactionDetail";
import { UploadCSV } from "./screens/UploadCSV";
import { RealTimeDetection } from "./screens/RealTimeDetection";
import { ModelInsights } from "./screens/ModelInsights";
import { Settings } from "./screens/Settings";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Layout,
    children: [
      { index: true, Component: Dashboard },
      { path: "transactions", Component: Transactions },
      { path: "transactions/:id", Component: TransactionDetail },
      { path: "upload", Component: UploadCSV },
      { path: "real-time", Component: RealTimeDetection },
      { path: "insights", Component: ModelInsights },
      { path: "settings", Component: Settings },
    ],
  },
]);
