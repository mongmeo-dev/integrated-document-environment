"use client";

import Link from "next/link";

import { authApi } from "@/api/client";

import styles from "./workspace-header.module.css";

const navigation = [
  { href: "/", label: "내 작업" },
  { href: "/documents/", label: "문서" },
  { href: "/history/", label: "전체 감사 이력" },
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
        aria-label="뉴다이브 문서 워크벤치 홈"
      >
        <span className={styles.brandMark}>ND</span>
        <span className={styles.brandCopy}>
          <strong>문서 워크벤치</strong>
          <small>GMP Document Control</small>
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
        <details className={styles.mobileMenu}>
          <summary aria-label="주 메뉴 열기">
            <svg
              aria-hidden="true"
              fill="none"
              height="20"
              viewBox="0 0 24 24"
              width="20"
            >
              <path d="M4 7h16M4 12h16M4 17h16" />
            </svg>
          </summary>
          <nav aria-label="모바일 주 메뉴">
            {navigation.map(({ href, label }) => (
              <Link
                aria-current={
                  isCurrentPath(currentPath, href) ? "page" : undefined
                }
                href={href}
                key={href}
              >
                {label}
              </Link>
            ))}
          </nav>
        </details>
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
            <input name="query" placeholder="문서 검색" type="search" />
            <kbd>Enter</kbd>
          </label>
        </form>
        <button
          aria-label="로그아웃"
          className={styles.userBadge}
          onClick={() => void logout()}
          type="button"
        >
          <span aria-hidden="true">내</span>
        </button>
      </div>
    </header>
  );
}
