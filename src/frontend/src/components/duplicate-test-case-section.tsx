"use client";

// Source assistance: OpenAI ChatGPT, 2026-08-25 (AI-05).
import { useEffect, useState } from "react";

import { USER_ROLE } from "@/constants/user-role";
import { ApiError } from "@/services/api";
import { listDuplicates, mergeDuplicate } from "@/services/testcases";
import type {
  DuplicateCandidate,
  DuplicateCandidateListResponse,
  TestCaseRecord,
  TestCaseStatus,
  User,
} from "@/types/api";
import { StateBlock } from "./state-block";

interface DuplicateTestCaseSectionProps {
  token: string;
  user: User;
  record: TestCaseRecord;
  onChanged: (record: TestCaseRecord) => void;
  onReload: () => Promise<void>;
}

const MERGEABLE_STATUSES: TestCaseStatus[] = ["draft", "in_review", "needs_fix"];

function message(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  return error instanceof Error ? error.message : "Không thể xử lý duplicate.";
}

function canMergeRole(user: User): boolean {
  return user.role === USER_ROLE.QA || user.role === USER_ROLE.MANAGER;
}

function canMergeStatus(status: TestCaseStatus): boolean {
  return MERGEABLE_STATUSES.includes(status);
}

export function DuplicateTestCaseSection(props: DuplicateTestCaseSectionProps) {
  const [result, setResult] = useState<DuplicateCandidateListResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [mergingId, setMergingId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    setNotice("");

    try {
      setResult(await listDuplicates(props.token, props.record.id));
    } catch (requestError) {
      setError(message(requestError));
    } finally {
      setLoading(false);
    }
  }

  async function merge(candidate: DuplicateCandidate) {
    const confirmed = window.confirm(
      `Gộp TC #${candidate.id} vào TC #${props.record.id}? ` + "Test case nguồn sẽ chuyển sang REJECTED.",
    );

    if (!confirmed) return;

    setMergingId(candidate.id);
    setError("");
    setNotice("");

    try {
      const response = await mergeDuplicate(props.token, props.record, candidate.id);

      props.onChanged(response.target);
      setResult(null);

      setNotice(
        `Đã gộp TC #${response.mergedSourceId} ` +
          `vào TC #${response.target.id} ` +
          `(${Math.round(response.similarity * 100)}%).`,
      );

      await props.onReload();
    } catch (requestError) {
      setError(message(requestError));
    } finally {
      setMergingId(null);
    }
  }

  useEffect(() => {
    queueMicrotask(() => {
      setResult(null);
      setError("");
      setNotice("");
    });
  }, [props.record.id]);

  return (
    <div className="subsection">
      <button className="secondary-button" disabled={loading || mergingId !== null} onClick={load} type="button">
        Kiểm tra Duplicate
      </button>

      <StateBlock loading={loading || mergingId !== null} error={error} />

      {notice ? <div className="state state-success">{notice}</div> : null}

      {result ? (
        <DuplicateResult
          result={result}
          record={props.record}
          user={props.user}
          mergingId={mergingId}
          onMerge={merge}
        />
      ) : null}
    </div>
  );
}

interface DuplicateResultProps {
  result: DuplicateCandidateListResponse;
  record: TestCaseRecord;
  user: User;
  mergingId: number | null;
  onMerge: (candidate: DuplicateCandidate) => Promise<void>;
}

function DuplicateResult(props: DuplicateResultProps) {
  const targetMergeable = canMergeRole(props.user) && canMergeStatus(props.record.status);

  return (
    <div className="subsection compact-subsection">
      <strong>Ngưỡng similarity: {props.result.threshold}</strong>

      <span className="muted-text">
        {props.result.embeddingModel} · {props.result.embeddingDimensions} dimensions
      </span>

      {props.result.data.length === 0 ? (
        <StateBlock empty emptyText="Không có duplicate candidate vượt ngưỡng." />
      ) : null}

      {props.result.data.map((item) => {
        const sourceMergeable = canMergeStatus(item.status);

        return (
          <div className="duplicate-row" key={item.id}>
            <span>
              TC #{item.id} · {item.summary}
            </span>

            <strong>{Math.round(item.similarity * 100)}%</strong>

            {canMergeRole(props.user) ? (
              <button
                className="ghost-button compact"
                disabled={!targetMergeable || !sourceMergeable || props.mergingId !== null}
                onClick={() => void props.onMerge(item)}
                type="button"
              >
                {props.mergingId === item.id ? "Đang gộp..." : "Gộp"}
              </button>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
