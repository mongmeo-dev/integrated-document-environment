"use client";

import { useState } from "react";

import { authApi } from "@/api/client";

import styles from "./login.module.css";

export function LoginForm() {
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isSubmitting) return;

    const formData = new FormData(event.currentTarget);
    const email = formData.get("email");
    const password = formData.get("password");

    if (typeof email !== "string" || typeof password !== "string") {
      setError("이메일과 비밀번호를 입력하세요.");
      return;
    }

    setError("");
    setIsSubmitting(true);

    try {
      await authApi.login({ loginRequest: { email, password } });
      window.location.replace("/documents/");
    } catch {
      setError("로그인하지 못했습니다. 이메일과 비밀번호를 확인하세요.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit}>
      <div className={styles.field}>
        <label htmlFor="email">이메일</label>
        <input
          autoComplete="email"
          id="email"
          name="email"
          required
          type="email"
        />
      </div>
      <div className={styles.field}>
        <label htmlFor="password">비밀번호</label>
        <input
          autoComplete="current-password"
          id="password"
          name="password"
          required
          type="password"
        />
      </div>
      {error ? (
        <p className={styles.error} role="alert">
          {error}
        </p>
      ) : null}
      <button className={styles.submit} disabled={isSubmitting} type="submit">
        {isSubmitting ? "로그인 중…" : "로그인"}
      </button>
      <p className={styles.notice}>
        계정 발급 또는 접근 권한이 필요하면 사내 관리자에게 문의하세요.
      </p>
    </form>
  );
}
