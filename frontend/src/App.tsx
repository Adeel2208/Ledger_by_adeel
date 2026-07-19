import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import AnalyticsPage from "@/features/analytics/AnalyticsPage";
import ApplyPage from "@/features/apply/ApplyPage";
import DashboardPage from "@/features/dashboard/DashboardPage";
import FounderPage from "@/features/founder/FounderPage";
import IntelligencePage from "@/features/intelligence/IntelligencePage";
import PatternsPage from "@/features/intelligence/PatternsPage";
import MemoPage from "@/features/memo/MemoPage";
import SourcingPage from "@/features/sourcing/SourcingPage";
import ThesisPage from "@/features/thesis/ThesisPage";
import TracePage from "@/features/trace/TracePage";

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/founders/:id" element={<FounderPage />} />
        <Route path="/founders/:id/intelligence" element={<IntelligencePage />} />
        <Route path="/patterns" element={<PatternsPage />} />
        <Route path="/memos/:id" element={<MemoPage />} />
        <Route path="/trace/:id" element={<TracePage />} />
        <Route path="/sourcing" element={<SourcingPage />} />
        <Route path="/channels" element={<AnalyticsPage />} />
        <Route path="/apply" element={<ApplyPage />} />
        <Route path="/thesis" element={<ThesisPage />} />
      </Routes>
    </AppShell>
  );
}
