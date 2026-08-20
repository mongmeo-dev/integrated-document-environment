"use client";

import {
  type FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import { approvalsApi, authApi } from "@/api/client";
import {
  ApprovalStatus,
  type ApprovalStepResponse,
  type ApprovalWorkflowAuditResponse,
  type ApprovalWorkflowResponse,
  type UserResponse,
} from "@/api/generated";

import styles from "./approvals.module.css";

type Workflow = ApprovalWorkflowResponse & { steps: ApprovalStepResponse[] };

function errorMessage(error: unknown) {
  return error instanceof Error
    ? error.message
    : "API 요청을 완료하지 못했습니다.";
}

function statusLabel(status: ApprovalStepResponse["status"]) {
  if (status === ApprovalStatus.Completed) return "완료";
  if (status === ApprovalStatus.Current) return "현재";
  return "대기";
}

function assigneeLabel(id: string, currentUser: UserResponse | null) {
  if (currentUser?.id === id) return `${currentUser.display_name} · 나`;
  return `담당자 ${id.slice(0, 8)}`;
}

function formatDate(value: string | null) {
  return value
    ? new Intl.DateTimeFormat("ko-KR", {
        dateStyle: "medium",
        timeStyle: "short",
      }).format(new Date(value))
    : "미완료";
}

export function ApprovalWorkspace({ documentId }: { documentId: string }) {
  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [audits, setAudits] = useState<ApprovalWorkflowAuditResponse[]>([]);
  const [currentUser, setCurrentUser] = useState<UserResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionId, setActionId] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [reason, setReason] = useState("");

  const loadWorkflow = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [loaded, user] = await Promise.all([
        approvalsApi.getDocumentApprovalWorkflow({ documentId }),
        authApi.getCurrentUser(),
      ]);
      const loadedAudits = await approvalsApi.listApprovalWorkflowAudits({
        workflowId: loaded.data.id,
      });
      setWorkflow({ ...loaded.data, steps: loaded.data.steps ?? [] });
      setAudits(loadedAudits.data);
      setCurrentUser(user.data);
    } catch (requestError) {
      setError(
        `승인 흐름을 불러오지 못했습니다: ${errorMessage(requestError)}`,
      );
      setWorkflow(null);
      setAudits([]);
    } finally {
      setLoading(false);
    }
  }, [documentId]);

  useEffect(() => {
    void loadWorkflow();
  }, [loadWorkflow]);

  const orderedSteps = useMemo(
    () => [...(workflow?.steps ?? [])].sort((a, b) => a.sequence - b.sequence),
    [workflow?.steps],
  );
  const currentStep = orderedSteps.find(
    (step) => step.status === ApprovalStatus.Current,
  );
  const isFinalCurrentStep = currentStep?.sequence === orderedSteps.length;

  async function approveCurrentStep() {
    if (!currentStep || currentStep.assignee_id !== currentUser?.id) return;
    setActionId(currentStep.id);
    setError(null);
    try {
      await approvalsApi.approveApprovalStep({
        stepId: currentStep.id,
      });
      await loadWorkflow();
    } catch (requestError) {
      setError(`승인 요청이 실패했습니다: ${errorMessage(requestError)}`);
    } finally {
      setActionId(null);
    }
  }

  async function saveStep(
    event: FormEvent<HTMLFormElement>,
    step: ApprovalStepResponse,
  ) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const nextReason = String(form.get("reason") ?? "").trim();
    if (!nextReason) {
      setError("흐름 변경 사유를 입력해야 저장할 수 있습니다.");
      return;
    }
    setActionId(step.id);
    setError(null);
    try {
      await approvalsApi.updateApprovalStep({
        stepId: step.id,
        approvalStepUpdate: {
          name: String(form.get("name") ?? "").trim(),
          assignee_id: String(form.get("assignee") ?? "").trim(),
          sequence: Number(form.get("sequence")),
          reason: nextReason,
        },
      });
      await loadWorkflow();
      setEditingId(null);
      setReason("");
    } catch (requestError) {
      setError(`승인 흐름 변경이 실패했습니다: ${errorMessage(requestError)}`);
    } finally {
      setActionId(null);
    }
  }

  async function startWorkflow() {
    if (!workflow || workflow.is_started) return;
    setActionId(workflow.id);
    setError(null);
    try {
      await approvalsApi.startApprovalWorkflow({ workflowId: workflow.id });
      await loadWorkflow();
    } catch (requestError) {
      setError(
        `승인 흐름을 시작하지 못했습니다: ${errorMessage(requestError)}`,
      );
    } finally {
      setActionId(null);
    }
  }

  if (!workflow) {
    return (
      <div className={styles.workspace} id="approval-workspace">
        <section className={styles.flowPanel} aria-busy={loading}>
          <h1>승인 흐름</h1>
          {loading && (
            <output className={styles.loading}>
              승인 흐름을 불러오는 중입니다.
            </output>
          )}
          {error && (
            <p className={styles.error} role="alert">
              {error}
            </p>
          )}
          {!loading && (
            <div className={styles.finalState}>
              <p>이 문서에 구성된 승인 흐름이 없습니다.</p>
              <a href={`/documents/${documentId}/approvals/configure/`}>
                승인 흐름 구성
              </a>
            </div>
          )}
        </section>
      </div>
    );
  }

  return (
    <div className={styles.workspace} id="approval-workspace">
      <section
        className={styles.flowPanel}
        aria-labelledby="approval-heading"
        aria-busy={loading}
      >
        <div className={styles.heading}>
          <div>
            <p className={styles.eyebrow}>문서별 순차 승인</p>
            <h1 id="approval-heading">승인 단계</h1>
            <p>각 단계가 완료되어야 다음 담당자에게 승인 권한이 열립니다.</p>
          </div>
          <div className={styles.workflowState}>
            <strong>
              {workflow.status === ApprovalStatus.Completed
                ? "문서 승인 완료"
                : "승인 진행 중"}
            </strong>
            <span>{orderedSteps.length}단계 구성</span>
          </div>
        </div>

        {loading && (
          <output className={styles.loading}>
            승인 흐름을 불러오는 중입니다.
          </output>
        )}
        {error && (
          <p className={styles.error} role="alert">
            {error}
          </p>
        )}

        <section className={styles.blocking} aria-labelledby="blocking-heading">
          <h2 id="blocking-heading">승인 차단 조건</h2>
          <ul>
            <li>
              이전 순서가 완료되기 전에는 다음 단계 승인을 진행할 수 없습니다.
            </li>
            <li>현재 담당자만 현재 단계를 승인할 수 있습니다.</li>
            <li>완료된 단계는 이름·담당자·순서를 변경할 수 없습니다.</li>
          </ul>
        </section>

        <ol className={styles.stepList} aria-label="승인 단계">
          {orderedSteps.map((step) => {
            const completed = step.status === ApprovalStatus.Completed;
            const editing = editingId === step.id;
            return (
              <li className={styles.step} key={step.id}>
                <div className={styles.sequence}>
                  <span className={styles.visuallyHidden}>순서 </span>
                  {step.sequence}
                </div>
                <div className={styles.stepBody}>
                  <div className={styles.stepSummary}>
                    <div>
                      <p className={`${styles.status} ${styles[step.status]}`}>
                        {statusLabel(step.status)}
                      </p>
                      <h2>{step.name}</h2>
                      <p>
                        <strong>담당자</strong>{" "}
                        {assigneeLabel(step.assignee_id, currentUser)} ·{" "}
                        <strong>순서</strong> {step.sequence} /{" "}
                        {orderedSteps.length}
                      </p>
                    </div>
                    {completed ? (
                      <button disabled type="button">
                        완료 단계는 편집할 수 없음
                      </button>
                    ) : (
                      <button
                        onClick={() => {
                          setEditingId(editing ? null : step.id);
                          setReason("");
                        }}
                        type="button"
                      >
                        {editing ? "편집 닫기" : "단계 편집"}
                      </button>
                    )}
                  </div>
                  {completed && (
                    <p className={styles.completedAt}>
                      완료 {formatDate(step.completed_at)}
                    </p>
                  )}
                  {editing && (
                    <form
                      className={styles.editForm}
                      onSubmit={(event) => saveStep(event, step)}
                    >
                      <label>
                        단계 이름
                        <input defaultValue={step.name} name="name" required />
                      </label>
                      <label>
                        담당자 ID
                        <input
                          defaultValue={step.assignee_id}
                          name="assignee"
                          required
                        />
                      </label>
                      <label>
                        순서
                        <input
                          defaultValue={step.sequence}
                          min="1"
                          max={orderedSteps.length}
                          name="sequence"
                          required
                          type="number"
                        />
                      </label>
                      <label className={styles.reason}>
                        변경 사유
                        <textarea
                          name="reason"
                          onChange={(event) => setReason(event.target.value)}
                          required
                          value={reason}
                        />
                      </label>
                      <div className={styles.formActions}>
                        <span>사유는 감사 이력에 기록됩니다.</span>
                        <button
                          disabled={!reason.trim() || actionId === step.id}
                          type="submit"
                        >
                          변경 저장
                        </button>
                      </div>
                    </form>
                  )}
                </div>
              </li>
            );
          })}
        </ol>

        {!workflow.is_started ? (
          <section className={styles.currentAction} aria-label="승인 흐름 시작">
            <div>
              <p>구성 완료</p>
              <strong>승인 흐름을 시작할 준비가 되었습니다.</strong>
              <span> 시작하면 첫 번째 담당자에게 승인 권한이 열립니다.</span>
            </div>
            <button
              disabled={actionId === workflow.id}
              onClick={startWorkflow}
              type="button"
            >
              {actionId === workflow.id ? "시작 중…" : "승인 흐름 시작"}
            </button>
          </section>
        ) : currentStep ? (
          <section className={styles.currentAction} aria-label="현재 승인 작업">
            <div>
              <p>현재 담당자</p>
              <strong>
                {assigneeLabel(currentStep.assignee_id, currentUser)}
              </strong>
              <span>
                {" "}
                {currentStep.name} · 순서 {currentStep.sequence}
              </span>
            </div>
            <button
              disabled={
                currentStep.assignee_id !== currentUser?.id ||
                actionId === currentStep.id
              }
              onClick={approveCurrentStep}
              type="button"
            >
              {actionId === currentStep.id
                ? "승인 처리 중"
                : isFinalCurrentStep
                  ? "최종 완료 승인"
                  : "현재 단계 승인"}
            </button>
          </section>
        ) : (
          <p className={styles.finalState}>
            모든 승인 단계가 완료되었습니다. 문서의 최종 승인 완료 상태입니다.
          </p>
        )}
      </section>

      <aside className={styles.auditPanel} aria-labelledby="audit-heading">
        <div>
          <p className={styles.eyebrow}>변경 전후 기록</p>
          <h2 id="audit-heading">흐름 변경 감사</h2>
        </div>
        <p>각 변경의 담당자, 사유, 이전 값과 변경 후 값을 보존합니다.</p>
        <ol className={styles.auditList}>
          {audits.map((audit) => (
            <li key={audit.id}>
              <time dateTime={audit.changed_at}>
                {formatDate(audit.changed_at)}
              </time>
              <strong>{assigneeLabel(audit.actor_id, currentUser)}</strong>
              <p>{audit.reason}</p>
              <dl>
                <div>
                  <dt>변경 전</dt>
                  <dd>{JSON.stringify(audit.before_json)}</dd>
                </div>
                <div>
                  <dt>변경 후</dt>
                  <dd>{JSON.stringify(audit.after_json)}</dd>
                </div>
              </dl>
            </li>
          ))}
        </ol>
      </aside>
    </div>
  );
}
