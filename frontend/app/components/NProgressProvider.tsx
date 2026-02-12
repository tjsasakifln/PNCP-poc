"use client";

import { Suspense, useEffect } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import NProgress from "nprogress";
import "nprogress/nprogress.css";

NProgress.configure({
  showSpinner: false,
  trickleSpeed: 200,
  minimum: 0.08,
  easing: "ease",
  speed: 400,
});

/** Inner component that uses useSearchParams (requires Suspense boundary). */
function NProgressListener({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  useEffect(() => {
    NProgress.done();
  }, [pathname, searchParams]);

  useEffect(() => {
    const handleStart = () => NProgress.start();
    window.addEventListener("beforeunload", handleStart);
    return () => {
      window.removeEventListener("beforeunload", handleStart);
    };
  }, []);

  return <>{children}</>;
}

/** Wraps children with NProgress navigation loading bar. Suspense-safe. */
export function NProgressProvider({ children }: { children: React.ReactNode }) {
  return (
    <Suspense fallback={<>{children}</>}>
      <NProgressListener>{children}</NProgressListener>
    </Suspense>
  );
}
