"use client";

import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { authApi } from "@/api/client";

type SessionGuardProps = {
  children: React.ReactNode;
};

function isUnauthorized(error: unknown) {
  return (
    typeof error === "object" &&
    error !== null &&
    "response" in error &&
    typeof error.response === "object" &&
    error.response !== null &&
    "status" in error.response &&
    error.response.status === 401
  );
}

export function SessionGuard({ children }: SessionGuardProps) {
  const pathname = usePathname();
  const isLoginPage = pathname === "/login" || pathname.startsWith("/login/");
  const [isChecking, setIsChecking] = useState(!isLoginPage);
  const [sessionError, setSessionError] = useState(false);

  useEffect(() => {
    let isActive = true;

    if (isLoginPage) {
      setIsChecking(false);
      setSessionError(false);
      return () => {
        isActive = false;
      };
    }

    setIsChecking(true);
    setSessionError(false);
    authApi
      .getCurrentUser()
      .then(() => {
        if (isActive) setIsChecking(false);
      })
      .catch((error: unknown) => {
        if (isUnauthorized(error)) {
          window.location.replace("/login/");
          return;
        }
        if (isActive) {
          setSessionError(true);
          setIsChecking(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [isLoginPage]);

  if (isLoginPage) return children;

  if (isChecking) {
    return (
      <main aria-busy="true" aria-live="polite">
        <p>로그인 상태를 확인하고 있습니다.</p>
      </main>
    );
  }

  if (sessionError) {
    return (
      <main role="alert">
        <p>로그인 상태를 확인하지 못했습니다. 잠시 후 다시 시도하세요.</p>
      </main>
    );
  }

  return children;
}
