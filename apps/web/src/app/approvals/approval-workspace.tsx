"use client";

import {
  type FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import { approvalsApi } from "@/api/client";
import {
  ApprovalStatus,
  type ApprovalStepResponse,
  type ApprovalWorkflowAuditResponse,
  type ApprovalWorkflowResponse,
} from "@/api/generated";

import styles from "./approvals.module.css";

const fixtureDocumentId = "ND-SRS-002";
const currentUserId = "user-km";

type Workflow = ApprovalWorkflowResponse & { steps: ApprovalStepResponse[] };

const fixtureWorkflow: Workflow = {
  id: "fixture-workflow-002",
  document_id: fixtureDocumentId,
  status: ApprovalStatus.Current,
  is_started: true,
  started_at: "2026-08-18T08:30:00Z",
  completed_at: null,
  created_at: "2026-08-18T08:15:00Z",
  updated_at: "2026-08-18T08:30:00Z",
  steps: [
    {
      id: "fixture-step-01",
      workflow_id: "fixture-workflow-002",
      name: "요구사항 검토",
      assignee_id: "user-jh",
      sequence: 1,
      status: ApprovalStatus.Completed,
      completed_at: "2026-08-18T08:30:00Z",
    },
    {
      id: "fixture-step-02",
      workflow_id: "fixture-workflow-002",
      name: "품질 보증 승인",
      assignee_id: currentUserId,
      sequence: 2,
      status: ApprovalStatus.Current,
      completed_at: null,
    },
    {
      id: "fixture-step-03",
      workflow_id: "fixture-workflow-002",
      name: "출시 책임자 확인",
      assignee_id: "user-ms",
      sequence: 3,
      status: ApprovalStatus.Pending,
      completed_at: null,
    },
  ],
};

const fixtureAudits: ApprovalWorkflowAuditResponse[] = [
  {
    id: "fixture-audit-02",
    workflow_id: fixtureWorkflow.id,
    actor_id: "user-jh",
    reason: "요구사항과 추적 근거를 검토하여 1단계 승인을 완료했습니다.",
    changed_at: "2026-08-18T08:30:00Z",
    before_json: { step: 1, status: "current" },
    after_json: { step: 1, status: "completed", next_step: 2 },
  },
  {
    id: "fixture-audit-01",
    workflow_id: fixtureWorkflow.id,
    actor_id: "user-km",
    reason: "품질 검토 이후 출시 책임자 확인을 마지막 순서로 지정했습니다.",
    changed_at: "2026-08-18T08:15:00Z",
    before_json: { steps: 2 },
    after_json: { steps: 3, sequence: [1, 2, 3] },
  },
];

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

function assigneeLabel(id: string) {
  const labels: Record<string, string> = {
    "user-jh": "JH · 요구사항 검토자",
    "user-km": "KM · 품질 보증",
    "user-ms": "MS · 출시 책임자",
  };
  return labels[id] ?? id;
}

function formatDate(value: string | null) {
  return value
    ? new Intl.DateTimeFormat("ko-KR", {
        dateStyle: "medium",
        timeStyle: "short",
      }).format(new Date(value))
    : "미완료";
}

export function ApprovalWorkspace() {
  const [searchParams] = useState(
    () =>
      new URLSearchParams(
        typeof window === "undefined" ? "" : window.location.search,
      ),
  );
  const documentId = searchParams.get("documentId");
  const workflowId = searchParams.get("workflowId");
  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [audits, setAudits] = useState<ApprovalWorkflowAuditResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionId, setActionId] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [reason, setReason] = useState("");
  const [showFixture, setShowFixture] = useState(false);

  const loadWorkflow = useCallback(async () => {
    if (showFixture) {
      setWorkflow(fixtureWorkflow);
      setAudits(fixtureAudits);
      return;
    }
    if (!documentId && !workflowId) {
      setWorkflow(null);
      setAudits([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const loaded = workflowId
        ? await approvalsApi.getApprovalWorkflow({ workflowId })
        : await approvalsApi.getDocumentApprovalWorkflow({
            documentId: documentId as string,
          });
      const loadedAudits = await approvalsApi.listApprovalWorkflowAudits({
        workflowId: loaded.data.id,
      });
      setWorkflow({ ...loaded.data, steps: loaded.data.steps ?? [] });
      setAudits(loadedAudits.data);
    } catch (requestError) {
      setError(
        `승인 흐름을 불러오지 못했습니다: ${errorMessage(requestError)}`,
      );
      setWorkflow(null);
      setAudits([]);
    } finally {
      setLoading(false);
    }
  }, [documentId, showFixture, workflowId]);

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
    if (!currentStep || currentStep.assignee_id !== currentUserId) return;
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
          {!loading && !error && (
            <>
              <p>
                URL에 documentId 또는 workflowId를 지정해 승인 흐름을
                조회하세요.
              </p>
              <button onClick={() => setShowFixture(true)} type="button">
                시안 보기
              </button>
            </>
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
            <p className={styles.eyebrow}>
              문서별 순차 승인 ·{" "}
              {showFixture && (
                <span className={styles.fixtureBadge}>Fixture</span>
              )}
            </p>
            <h1 id="approval-heading">{workflow.document_id} · 순차 승인</h1>
            <p>각 단계가 완료되어야 다음 담당자에게 승인 권한이 열립니다.</p>
          </div>
          <div className={styles.workflowState}>
            <strong>
              {workflow.status === ApprovalStatus.Completed
                ? "문서 승인 완료"
                : "승인 진행 중"}
            </strong>
            <span>흐름 ID {workflow.id}</span>
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
                        {assigneeLabel(step.assignee_id)} ·{" "}
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

        {currentStep ? (
          <section className={styles.currentAction} aria-label="현재 승인 작업">
            <div>
              <p>현재 담당자</p>
              <strong>{assigneeLabel(currentStep.assignee_id)}</strong>
              <span>
                {" "}
                {currentStep.name} · 순서 {currentStep.sequence}
              </span>
            </div>
            <button
              disabled={
                currentStep.assignee_id !== currentUserId ||
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
              <strong>{assigneeLabel(audit.actor_id)}</strong>
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
