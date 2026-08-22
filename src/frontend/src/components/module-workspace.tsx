"use client";

// Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).
import { FormEvent, useCallback, useEffect, useState } from "react";

import { ApiError } from "@/services/api";
import { createModule, getCoverage, listModules, updateModule } from "@/services/modules";
import { exportTestCases } from "@/services/testcases";
import type { CoverageResponse, ModuleRecord, User } from "@/types/api";
import { FieldError, StateBlock } from "./state-block";

interface ModuleWorkspaceProps {
  token: string;
  user: User;
}

function errorText(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  return error instanceof Error ? error.message : "Không thể xử lý module.";
}

function useModuleList(token: string) {
  const [modules, setModules] = useState<ModuleRecord[]>([]);
  const [selectedId, setSelectedId] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await listModules(token);
      setModules(response.data);
      setSelectedId(response.data[0]?.id ?? 0);
    } catch (requestError) {
      setError(errorText(requestError));
    } finally {
      setLoading(false);
    }
  }, [token]);
  useEffect(() => {
    queueMicrotask(() => void load());
  }, [load]);
  return { modules, setModules, selectedId, setSelectedId, loading, error };
}

function useActionState() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await action();
    } catch (requestError) {
      setError(errorText(requestError));
    } finally {
      setBusy(false);
    }
  }
  return { busy, error, notice, setNotice, run };
}

export function ModuleWorkspace({ token, user }: ModuleWorkspaceProps) {
  const list = useModuleList(token);
  const action = useActionState();
  const [name, setName] = useState("");
  const [coverage, setCoverage] = useState<CoverageResponse | null>(null);
  const nameError = name.length > 0 && name.trim().length < 2 ? "Tên module phải có ít nhất 2 ký tự." : "";
  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await action.run(async () => {
      const created = await createModule(token, name, null);
      list.setModules((current) => [...current, created]);
      list.setSelectedId(created.id);
      setName("");
      action.setNotice("Đã tạo module.");
    });
  }
  async function rename() {
    if (!list.selectedId || !name.trim()) return;
    await action.run(async () => {
      const updated = await updateModule(token, list.selectedId, name.trim());
      list.setModules((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      setName("");
      action.setNotice("Đã cập nhật module.");
    });
  }
  return (
    <div className="two-column">
      <ManagementPanel
        user={user}
        list={list}
        name={name}
        setName={setName}
        nameError={nameError}
        busy={action.busy}
        create={create}
        rename={rename}
      />
      <CoveragePanel
        token={token}
        user={user}
        moduleId={list.selectedId}
        coverage={coverage}
        setCoverage={setCoverage}
        action={action}
      />
    </div>
  );
}

interface ManagementProps {
  user: User;
  list: ReturnType<typeof useModuleList>;
  name: string;
  setName: (value: string) => void;
  nameError: string;
  busy: boolean;
  create: (event: FormEvent<HTMLFormElement>) => Promise<void>;
  rename: () => Promise<void>;
}

function ManagementPanel({ user, list, name, setName, nameError, busy, create, rename }: ManagementProps) {
  const canManage = user.role === "manager";
  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <div className="eyebrow">NC-06</div>
          <h3>Tổ chức theo Module</h3>
        </div>
      </div>
      <StateBlock
        loading={list.loading}
        error={list.error}
        empty={!list.loading && list.modules.length === 0}
        emptyText="Chưa có module."
      />
      {list.modules.length > 0 ? (
        <label>
          Module
          <select value={list.selectedId} onChange={(event) => list.setSelectedId(Number(event.target.value))}>
            {list.modules.map((module) => (
              <option key={module.id} value={module.id}>
                {module.name}
              </option>
            ))}
          </select>
        </label>
      ) : null}
      {canManage ? (
        <form className="stack-form compact-form" onSubmit={create}>
          <label>
            Tên module
            <input value={name} onChange={(event) => setName(event.target.value)} minLength={2} maxLength={150} />
            <FieldError message={nameError} />
          </label>
          <div className="button-row">
            <button className="primary-button" disabled={busy || !name.trim() || Boolean(nameError)} type="submit">
              Tạo module
            </button>
            <button
              className="secondary-button"
              disabled={busy || !list.selectedId || !name.trim() || Boolean(nameError)}
              onClick={() => void rename()}
              type="button"
            >
              Đổi tên module đang chọn
            </button>
          </div>
        </form>
      ) : (
        <div className="help-box">Chỉ Manager được tạo/sửa module và quản lý tags.</div>
      )}
    </section>
  );
}

interface CoverageProps {
  token: string;
  user: User;
  moduleId: number;
  coverage: CoverageResponse | null;
  setCoverage: (value: CoverageResponse | null) => void;
  action: ReturnType<typeof useActionState>;
}

function CoveragePanel({ token, user, moduleId, coverage, setCoverage, action }: CoverageProps) {
  const canCoverage = user.role === "qa" || user.role === "manager";
  async function load() {
    if (moduleId) await action.run(async () => setCoverage(await getCoverage(token, moduleId)));
  }
  async function exportFile(format: "csv" | "xlsx") {
    if (!moduleId) return;
    await action.run(async () => {
      await exportTestCases(token, moduleId, format);
      action.setNotice(`Đã tạo file ${format.toUpperCase()} từ các test case APPROVED.`);
    });
  }
  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <div className="eyebrow">NC-07 · NC-12</div>
          <h3>Coverage & Export</h3>
        </div>
      </div>
      <div className="button-row wrap-row">
        <button
          className="secondary-button"
          disabled={action.busy || !moduleId || !canCoverage}
          onClick={() => void load()}
          type="button"
        >
          Xem coverage
        </button>
        <button
          className="secondary-button"
          disabled={action.busy || !moduleId || user.role === "admin"}
          onClick={() => void exportFile("csv")}
          type="button"
        >
          Export CSV
        </button>
        <button
          className="secondary-button"
          disabled={action.busy || !moduleId || user.role === "admin"}
          onClick={() => void exportFile("xlsx")}
          type="button"
        >
          Export XLSX
        </button>
      </div>
      {coverage ? (
        <CoverageCard coverage={coverage} />
      ) : (
        <StateBlock empty emptyText="Chọn module và bấm Xem coverage." />
      )}
      {action.error ? <div className="state state-error">{action.error}</div> : null}
      {action.notice ? <div className="state state-success">{action.notice}</div> : null}
    </section>
  );
}

function CoverageCard({ coverage }: { coverage: CoverageResponse }) {
  return (
    <div className="coverage-card">
      <div className="coverage-score">{coverage.requirementCoveragePercent}%</div>
      <div>
        <strong>
          {coverage.coveredRequirements}/{coverage.totalRequirements}
        </strong>
        <span> requirements có test case</span>
      </div>
      <div>
        <strong>
          {coverage.approvedTestCases}/{coverage.totalTestCases}
        </strong>
        <span> test case đã APPROVED</span>
      </div>
      <div className="status-grid">
        {Object.entries(coverage.statusCounts).map(([status, count]) => (
          <div key={status}>
            <span>{status}</span>
            <strong>{count}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}
