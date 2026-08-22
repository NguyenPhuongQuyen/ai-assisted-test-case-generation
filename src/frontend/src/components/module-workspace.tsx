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

function ManagementPanel(props: ManagementProps) {
  const canManage = props.user.role === "manager";

  return (
    <section className="panel">
      <ManagementHeader />

      <StateBlock
        loading={props.list.loading}
        error={props.list.error}
        empty={!props.list.loading && props.list.modules.length === 0}
        emptyText="Chưa có module."
      />

      <ManagementModuleSelect list={props.list} />

      {canManage ? (
        <ManagementForm
          list={props.list}
          name={props.name}
          setName={props.setName}
          nameError={props.nameError}
          busy={props.busy}
          create={props.create}
          rename={props.rename}
        />
      ) : (
        <div className="help-box">Chỉ Manager được tạo/sửa module và quản lý tags.</div>
      )}
    </section>
  );
}

function ManagementHeader() {
  return (
    <div className="panel-heading">
      <div>
        <div className="eyebrow">NC-06</div>
        <h3>Tổ chức theo Module</h3>
      </div>
    </div>
  );
}

function ManagementModuleSelect({ list }: { list: ReturnType<typeof useModuleList> }) {
  if (list.modules.length === 0) return null;

  return (
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
  );
}

function ManagementForm({ list, name, setName, nameError, busy, create, rename }: Omit<ManagementProps, "user">) {
  const invalid = busy || !name.trim() || Boolean(nameError);

  return (
    <form className="stack-form compact-form" onSubmit={create}>
      <label>
        Tên module
        <input value={name} onChange={(event) => setName(event.target.value)} minLength={2} maxLength={150} />
        <FieldError message={nameError} />
      </label>

      <div className="button-row">
        <button className="primary-button" disabled={invalid} type="submit">
          Tạo module
        </button>

        <button
          className="secondary-button"
          disabled={invalid || !list.selectedId}
          onClick={() => void rename()}
          type="button"
        >
          Đổi tên module đang chọn
        </button>
      </div>
    </form>
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

function useCoverageActions(props: CoverageProps) {
  async function load() {
    if (!props.moduleId) return;

    await props.action.run(async () => props.setCoverage(await getCoverage(props.token, props.moduleId)));
  }

  async function exportFile(format: "csv" | "xlsx") {
    if (!props.moduleId) return;

    await props.action.run(async () => {
      await exportTestCases(props.token, props.moduleId, format);

      props.action.setNotice(`Đã tạo file ${format.toUpperCase()} từ các test case APPROVED.`);
    });
  }

  return {
    load,
    exportFile,
  };
}

function useCoveragePanelActions(props: CoverageProps) {
  async function load() {
    if (!props.moduleId) return;

    await props.action.run(async () => props.setCoverage(await getCoverage(props.token, props.moduleId)));
  }

  async function exportFile(format: "csv" | "xlsx") {
    if (!props.moduleId) return;

    await props.action.run(async () => {
      await exportTestCases(props.token, props.moduleId, format);

      props.action.setNotice(`Đã tạo file ${format.toUpperCase()} từ các test case APPROVED.`);
    });
  }

  return {
    load,
    exportFile,
  };
}

function CoveragePanel(props: CoverageProps) {
  const canCoverage = props.user.role === "qa" || props.user.role === "manager";

  const actions = useCoveragePanelActions(props);

  return (
    <section className="panel">
      <CoverageHeader />

      <CoverageActionButtons
        user={props.user}
        moduleId={props.moduleId}
        busy={props.action.busy}
        canCoverage={canCoverage}
        onLoad={actions.load}
        onExport={actions.exportFile}
      />

      {props.coverage ? (
        <CoverageCard coverage={props.coverage} />
      ) : (
        <StateBlock empty emptyText="Chọn module và bấm Xem coverage." />
      )}

      <CoverageMessages action={props.action} />
    </section>
  );
}

function CoverageHeader() {
  return (
    <div className="panel-heading">
      <div>
        <div className="eyebrow">NC-07 · NC-12</div>
        <h3>Coverage & Export</h3>
      </div>
    </div>
  );
}

interface CoverageActionButtonsProps {
  user: User;
  moduleId: number;
  busy: boolean;
  canCoverage: boolean;
  onLoad: () => Promise<void>;
  onExport: (format: "csv" | "xlsx") => Promise<void>;
}

function CoverageActionButtons(props: CoverageActionButtonsProps) {
  const exportDisabled = props.busy || !props.moduleId || props.user.role === "admin";

  return (
    <div className="button-row wrap-row">
      <button
        className="secondary-button"
        disabled={props.busy || !props.moduleId || !props.canCoverage}
        onClick={() => void props.onLoad()}
        type="button"
      >
        Xem coverage
      </button>

      <button
        className="secondary-button"
        disabled={exportDisabled}
        onClick={() => void props.onExport("csv")}
        type="button"
      >
        Export CSV
      </button>

      <button
        className="secondary-button"
        disabled={exportDisabled}
        onClick={() => void props.onExport("xlsx")}
        type="button"
      >
        Export XLSX
      </button>
    </div>
  );
}

function CoverageMessages({ action }: { action: ReturnType<typeof useActionState> }) {
  return (
    <>
      {action.error ? <div className="state state-error">{action.error}</div> : null}

      {action.notice ? <div className="state state-success">{action.notice}</div> : null}
    </>
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
