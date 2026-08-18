import styles from "./login.module.css";
import { LoginForm } from "./login-form";

export default function LoginPage() {
  return (
    <main className={styles.page}>
      <section className={styles.panel} aria-labelledby="login-title">
        <p className={styles.eyebrow}>NEUDIVE DOCUMENT IDE</p>
        <h1 id="login-title">사내 계정으로 로그인</h1>
        <p className={styles.description}>
          뉴다이브 임직원 전용 문서 작업 환경입니다.
        </p>
        <LoginForm />
      </section>
    </main>
  );
}
