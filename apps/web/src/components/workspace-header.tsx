"use client";

import Link from "next/link";

import { authApi } from "@/api/client";

import styles from "./workspace-header.module.css";

const navigation = [
  { href: "/", label: "작업공간" },
  { href: "/documents/", label: "문서" },
  { href: "/relations/", label: "관계·영향" },
  { href: "/evidence/", label: "제품·검증 근거" },
  { href: "/approvals/", label: "승인 흐름" },
  { href: "/history/", label: "변경 이력" },
];

function isCurrentPath(currentPath: string, href: string) {
  return href === "/"
    ? currentPath === href
    : currentPath === href || currentPath.startsWith(href);
}

export function WorkspaceHeader({ currentPath }: { currentPath: string }) {
  async function logout() {
    await authApi.logout();
    window.location.replace("/login/");
  }

  return (
    <header className={styles.header}>
      <Link
        className={styles.brand}
        href="/"
        aria-label="Document Workspace 홈"
      >
        <span className={styles.brandMark}>ND</span>
        <span className={styles.brandCopy}>
          <strong>Document Workspace</strong>
          <small>GMP Development</small>
        </span>
      </Link>

      <nav aria-label="주 메뉴" className={styles.primaryNav}>
        {navigation.map(({ href, label }) => (
          <Link
            aria-current={isCurrentPath(currentPath, href) ? "page" : undefined}
            href={href}
            key={href}
          >
            {label}
          </Link>
        ))}
      </nav>

      <div className={styles.headerTools}>
        <form action="/documents/" className={styles.search} method="get">
          <label>
            <svg
              aria-hidden="true"
              fill="none"
              height="14"
              viewBox="0 0 24 24"
              width="14"
            >
              <circle cx="11" cy="11" r="7" />
              <path d="m20 20-4-4" />
            </svg>
            <span className={styles.visuallyHidden}>문서 검색</span>
            <input
              name="query"
              placeholder="문서명 또는 문서 ID 검색"
              type="search"
            />
            <kbd>Enter</kbd>
          </label>
        </form>
        <button
          aria-label="로그아웃"
          className={styles.userBadge}
          onClick={() => void logout()}
          type="button"
        >
          내
        </button>
      </div>
    </header>
  );
}
