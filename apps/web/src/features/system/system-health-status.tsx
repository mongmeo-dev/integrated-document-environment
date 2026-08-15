"use client";

import styles from "@/app/page.module.css";

import { useHealthQuery } from "./use-health-query";

export function SystemHealthStatus() {
  const health = useHealthQuery();

  const label = health.isPending
    ? "시스템 상태 확인 중"
    : health.isSuccess
      ? "모든 시스템 정상"
      : "API 연결 확인 필요";

  return (
    <div
      aria-live="polite"
      className={
        health.isError ? styles.systemStatusError : styles.systemStatus
      }
    >
      <span aria-hidden="true" />
      {label}
    </div>
  );
}
