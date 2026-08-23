"use client";

// Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).
import { USER_ROLE } from "@/constants/user-role";
import { useEffect, useState } from "react";

import { ApiError } from "@/services/api";
import { updateTags } from "@/services/modules";
import { compareVersions, listDuplicates, listVersions, restoreVersion } from "@/services/testcases";
import type {
  DuplicateCandidateListResponse,
  TestCaseRecord,
  TestCaseVersion,
  User,
  VersionCompareResponse,
} from "@/types/api";
import { StateBlock } from "./state-block";

interface TestCaseInsightsProps {
  token: string;
  user: User;
  record: TestCaseRecord | null;
  onChanged: (record: TestCaseRecord) => void;
}

function message(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  return error instanceof Error ? error.message : "Không thể tải dữ liệu hỗ trợ review.";
}

function VersionOptions({ versions }: { versions: TestCaseVersion[] }) {
  return versions.map((version) => (
    <option key={version.versionNumber} value={version.versionNumber}>
      Version {version.versionNumber}
    </option>
  ));
}

export function TestCaseInsights({ token, user, record, onChanged }: TestCaseInsightsProps) {
  if (!record) return null;
  return (
    <section className="panel insights-panel">
      <div className="panel-heading">
        <div>
          <div className="eyebrow">NC-05 · NC-08</div>
          <h3>Duplicate & Version</h3>
        </div>
      </div>
      <DuplicateSection token={token} record={record} />
      <VersionSection token={token} record={record} onChanged={onChanged} />
      {user.role === USER_ROLE.MANAGER ? <TagsSection token={token} record={record} onChanged={onChanged} /> : null}
    </section>
  );
}

function DuplicateSection({ token, record }: { token: string; record: TestCaseRecord }) {
  const [result, setResult] = useState<DuplicateCandidateListResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      setResult(await listDuplicates(token, record.id));
    } catch (requestError) {
      setError(message(requestError));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    queueMicrotask(() => {
      setResult(null);
      setError("");
    });
  }, [record.id]);

  return (
    <div className="subsection">
      <button className="secondary-button" disabled={loading} onClick={load} type="button">
        Kiểm tra Duplicate
      </button>
      <StateBlock loading={loading} error={error} />
      {result ? <DuplicateResult result={result} /> : null}
    </div>
  );
}

function DuplicateResult({ result }: { result: DuplicateCandidateListResponse }) {
  return (
    <div className="subsection compact-subsection">
      <strong>Ngưỡng similarity: {result.threshold}</strong>
      <span className="muted-text">
        {result.embeddingModel} · {result.embeddingDimensions} dimensions
      </span>
      {result.data.length === 0 ? <StateBlock empty emptyText="Không có duplicate candidate vượt ngưỡng." /> : null}
      {result.data.map((item) => (
        <div className="duplicate-row" key={item.id}>
          <span>
            TC #{item.id} · {item.summary}
          </span>
          <strong>{Math.round(item.similarity * 100)}%</strong>
        </div>
      ))}
    </div>
  );
}

function useVersionActionState() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function run(action: () => Promise<void>) {
    setLoading(true);
    setError("");
    setNotice("");

    try {
      await action();
    } catch (requestError) {
      setError(message(requestError));
    } finally {
      setLoading(false);
    }
  }

  return {
    loading,
    error,
    notice,
    setError,
    setNotice,
    run,
  };
}

function resetVersionHistory(
  setVersions: (value: TestCaseVersion[]) => void,
  setComparison: (value: VersionCompareResponse | null) => void,
  setError: (value: string) => void,
  setNotice: (value: string) => void,
) {
  setVersions([]);
  setComparison(null);
  setError("");
  setNotice("");
}

function useVersionHistory(token: string, record: TestCaseRecord, onChanged: (record: TestCaseRecord) => void) {
  const [versions, setVersions] = useState<TestCaseVersion[]>([]);
  const [comparison, setComparison] = useState<VersionCompareResponse | null>(null);
  const [fromVersion, setFromVersion] = useState(1);
  const [toVersion, setToVersion] = useState(1);
  const { loading, error, notice, setError, setNotice, run } = useVersionActionState();

  async function load() {
    await run(async () => {
      const response = await listVersions(token, record.id);
      setVersions(response.data);
      setFromVersion(response.data[0]?.versionNumber ?? 1);
      setToVersion(response.data.at(-1)?.versionNumber ?? 1);
    });
  }

  async function compare() {
    await run(async () => setComparison(await compareVersions(token, record.id, fromVersion, toVersion)));
  }

  async function restore(versionNumber: number) {
    await run(async () => {
      onChanged(await restoreVersion(token, record, versionNumber));
      setNotice(`Đã restore version ${versionNumber}; trạng thái chuyển về NEEDS_FIX để review lại.`);
    });
  }

  useEffect(() => {
    queueMicrotask(() => resetVersionHistory(setVersions, setComparison, setError, setNotice));
  }, [record.id, setError, setNotice]);

  return {
    versions,
    comparison,
    fromVersion,
    toVersion,
    loading,
    error,
    notice,
    setFromVersion,
    setToVersion,
    load,
    compare,
    restore,
  };
}

function VersionSection(props: { token: string; record: TestCaseRecord; onChanged: (record: TestCaseRecord) => void }) {
  const state = useVersionHistory(props.token, props.record, props.onChanged);
  return (
    <div className="subsection">
      <button className="secondary-button" disabled={state.loading} onClick={state.load} type="button">
        Lịch sử phiên bản
      </button>
      <StateBlock loading={state.loading} error={state.error} />
      {state.versions.length > 0 ? <VersionControls state={state} /> : null}
      {state.comparison ? <pre className="diff-box">{JSON.stringify(state.comparison.changes, null, 2)}</pre> : null}
      {state.notice ? <div className="state state-success">{state.notice}</div> : null}
    </div>
  );
}

type VersionState = ReturnType<typeof useVersionHistory>;

function VersionControls({ state }: { state: VersionState }) {
  return (
    <div className="subsection compact-subsection">
      <div className="compare-controls">
        <select
          aria-label="Phiên bản nguồn để so sánh"
          value={state.fromVersion}
          onChange={(event) => state.setFromVersion(Number(event.target.value))}
        >
          <VersionOptions versions={state.versions} />
        </select>
        <span>→</span>
        <select
          aria-label="Phiên bản đích để so sánh"
          value={state.toVersion}
          onChange={(event) => state.setToVersion(Number(event.target.value))}
        >
          <VersionOptions versions={state.versions} />
        </select>
        <button className="ghost-button compact" disabled={state.loading} onClick={state.compare} type="button">
          Compare
        </button>
      </div>
      <div className="version-list">
        {state.versions.map((version) => (
          <div className="version-row" key={version.versionNumber}>
            <span>
              v{version.versionNumber} ·{" "}
              {new Date(version.createdAt).toLocaleString("vi-VN", {
                timeZone: "Asia/Ho_Chi_Minh",
                day: "2-digit",
                month: "2-digit",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
                hour12: false,
              })}
            </span>
            <button
              className="ghost-button compact"
              disabled={state.loading}
              onClick={() => state.restore(version.versionNumber)}
              type="button"
            >
              Restore
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

function TagsSection(props: { token: string; record: TestCaseRecord; onChanged: (record: TestCaseRecord) => void }) {
  const [tags, setTags] = useState(props.record.tags.join(", "));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    queueMicrotask(() => setTags(props.record.tags.join(", ")));
  }, [props.record.id, props.record.tags]);

  async function save() {
    setLoading(true);
    setError("");
    setNotice("");
    try {
      const normalized = tags
        .split(",")
        .map((tag) => tag.trim())
        .filter(Boolean);
      const response = await updateTags(props.token, props.record.module_id, props.record.id, normalized);
      props.onChanged({ ...props.record, tags: response.tags });
      setNotice("Đã cập nhật tag.");
    } catch (requestError) {
      setError(message(requestError));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="subsection">
      <label>
        Tags
        <input
          value={tags}
          onChange={(event) => setTags(event.target.value)}
          placeholder="boundary, payment, regression"
        />
      </label>
      <button className="secondary-button" disabled={loading} onClick={save} type="button">
        Lưu tags
      </button>
      <StateBlock loading={loading} error={error} />
      {notice ? <div className="state state-success">{notice}</div> : null}
    </div>
  );
}
