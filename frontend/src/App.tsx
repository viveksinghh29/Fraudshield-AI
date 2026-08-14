import { Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "@/components/layout/AppLayout";
import { ProtectedRoute } from "@/routes/ProtectedRoute";

import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import SinglePrediction from "@/pages/SinglePrediction";
import BatchPrediction from "@/pages/BatchPrediction";
import Transactions from "@/pages/Transactions";
import Analytics from "@/pages/Analytics";
import ModelPerformance from "@/pages/ModelPerformance";
import ShapVisualizations from "@/pages/ShapVisualizations";
import Assistant from "@/pages/Assistant";
import Profile from "@/pages/Profile";
import Settings from "@/pages/Settings";

function Protected({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute>
      <AppLayout>{children}</AppLayout>
    </ProtectedRoute>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route path="/" element={<Protected><Dashboard /></Protected>} />
      <Route path="/predict" element={<Protected><SinglePrediction /></Protected>} />
      <Route path="/batch" element={<Protected><BatchPrediction /></Protected>} />
      <Route path="/transactions" element={<Protected><Transactions /></Protected>} />
      <Route path="/analytics" element={<Protected><Analytics /></Protected>} />
      <Route path="/model-performance" element={<Protected><ModelPerformance /></Protected>} />
      <Route path="/shap" element={<Protected><ShapVisualizations /></Protected>} />
      <Route path="/assistant" element={<Protected><Assistant /></Protected>} />
      <Route path="/profile" element={<Protected><Profile /></Protected>} />
      <Route path="/settings" element={<Protected><Settings /></Protected>} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
