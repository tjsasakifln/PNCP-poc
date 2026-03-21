import { ErrorBoundary } from "../../components/ErrorBoundary";

/** DEBT-FE-007: ErrorBoundary wrapping for onboarding page */
export default function OnboardingLayout({ children }: { children: React.ReactNode }) {
  return <ErrorBoundary pageName="onboarding">{children}</ErrorBoundary>;
}
