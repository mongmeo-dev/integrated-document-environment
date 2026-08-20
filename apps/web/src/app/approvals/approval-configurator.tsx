"use client";

import { useState } from "react";

import { approvalsApi } from "@/api/client";

import styles from "./approvals.module.css";

type DraftStep = {
  name: string;
  assigneeId: string;
};

export function ApprovalConfigurator({ documentId }: { documentId: string }) {
  const [steps, setSteps] = useState<DraftStep[]>([
    { name: "문서 검토", assigneeId: "" },
  ]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function updateStep(index: number, field: keyof DraftStep, value: string) {
    setSteps((current) =>
      current.map((step, stepIndex) =>
        stepIndex === index ? { ...step, [field]: value } : step,
      ),
    );
  }

  async function createWorkflow(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const completeSteps = steps.filter(
      (step) => step.name.trim() && step.assigneeId.trim(),
    );
    if (completeSteps.length !== steps.length) {
      setError("모든 단계의 이름과 담당자 ID를 입력하세요.");
      return;
    }

    setPending(true);
    setError(null);
    try {
      await approvalsApi.createApprovalWorkflow({
        approvalWorkflowCreate: {
          document_id: documentId,
          steps: completeSteps.map((step, index) => ({
            assignee_id: step.assigneeId.trim(),
            name: step.name.trim(),
            sequence: index + 1,
          })),
        },
      });
      window.location.assign(`/documents/${documentId}/approvals/`);
    } catch {
      setError("승인 흐름을 만들지 못했습니다. 이미 흐름이 있는지 확인하세요.");
      setPending(false);
    }
  }

  return (
    <section className={styles.configuration}>
      <header>
        <p className={styles.eyebrow}>승인 흐름 구성</p>
        <h1>단계와 담당자 지정</h1>
        <p>
          위에서 아래 순서대로 승인이 진행됩니다. 흐름을 시작한 뒤 완료된 단계는
          변경할 수 없습니다.
        </p>
      </header>
      <form onSubmit={createWorkflow}>
        <ol className={styles.configurationSteps}>
          {steps.map((step, index) => (
            <li key={`step-${index + 1}`}>
              <span>{index + 1}</span>
              <label>
                단계 이름
                <input
                  onChange={(event) =>
                    updateStep(index, "name", event.target.value)
                  }
                  required
                  value={step.name}
                />
              </label>
              <label>
                담당자 ID
                <input
                  onChange={(event) =>
                    updateStep(index, "assigneeId", event.target.value)
                  }
                  required
                  value={step.assigneeId}
                />
              </label>
              <button
                disabled={steps.length === 1}
                onClick={() =>
                  setSteps((current) =>
                    current.filter((_, stepIndex) => stepIndex !== index),
                  )
                }
                type="button"
              >
                단계 제거
              </button>
            </li>
          ))}
        </ol>
        <div className={styles.configurationActions}>
          <button
            onClick={() =>
              setSteps((current) => [...current, { name: "", assigneeId: "" }])
            }
            type="button"
          >
            단계 추가
          </button>
          <button disabled={pending} type="submit">
            {pending ? "흐름 만드는 중…" : "승인 흐름 만들기"}
          </button>
        </div>
        {error && (
          <p className={styles.error} role="alert">
            {error}
          </p>
        )}
      </form>
    </section>
  );
}
