"use client";

// Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).
import { USER_ROLE } from "@/constants/user-role";
import { FormEvent, useCallback, useEffect, useState } from "react";

import { ApiError } from "@/services/api";
import { listModules } from "@/services/modules";
import { createRequirement, listRequirements, updateRequirement } from "@/services/requirements";
import { generateTestCases, getGenerationJob } from "@/services/testcases";
import type { GenerationJob, ModuleRecord, RequirementRecord, User } from "@/types/api";
import { JobPanel, RequirementHeader, RequirementModuleField } from "./requirement-view-parts";
import { FieldError, StateBlock } from "./state-block";

interface RequirementWorkspaceProps {
  token: string;
  user: User;
}

function toMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  return error instanceof Error ? error.message : "Đã có lỗi xảy ra.";
}

async function waitForJob(token: string, job: GenerationJob): Promise<GenerationJob> {
  let current = job;
  for (let attempt = 0; attempt < 40; attempt += 1) {
    if (current.status === "completed" || current.status === "failed") return current;
    await new Promise((resolve) => window.setTimeout(resolve, 1500));
    current = await getGenerationJob(token, job.id);
  }
  return current;
}

function useModules(token: string) {
  const [modules, setModules] = useState<ModuleRecord[]>([]);
  const [moduleId, setModuleId] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await listModules(token);
      setModules(response.data);
      setModuleId(response.data[0]?.id ?? 0);
    } catch (requestError) {
      setError(toMessage(requestError));
    } finally {
      setLoading(false);
    }
  }, [token]);
  useEffect(() => {
    queueMicrotask(() => void load());
  }, [load]);
  return { modules, moduleId, setModuleId, loading, error };
}

function useRequirements(token: string, moduleId: number) {
  const [requirements, setRequirements] = useState<RequirementRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!moduleId) {
      setRequirements([]);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await listRequirements(token, moduleId);
      setRequirements(response.data);
    } catch (requestError) {
      setError(toMessage(requestError));
    } finally {
      setLoading(false);
    }
  }, [token, moduleId]);

  useEffect(() => {
    queueMicrotask(() => void load());
  }, [load]);

  return { requirements, loading, error, load };
}

function useRequirementForm(token: string, moduleId: number, reloadRequirements: () => Promise<void>) {
  const [content, setContent] = useState("");
  const [criteria, setCriteria] = useState("");
  const [current, setCurrent] = useState<RequirementRecord | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const startNew = useCallback(() => {
    setContent("");
    setCriteria("");
    setCurrent(null);
    setError("");
    setNotice("");
  }, []);

  function selectRequirement(requirement: RequirementRecord) {
    setCurrent(requirement);
    setContent(requirement.content);
    setCriteria(requirement.acceptance_criteria ?? "");
    setError("");
    setNotice("");
  }

  useEffect(() => {
    queueMicrotask(startNew);
  }, [moduleId, startNew]);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setNotice("");
    try {
      const saved = current
        ? await updateRequirement(token, current, content, criteria)
        : await createRequirement(token, moduleId, content, criteria);
      setCurrent(saved);
      await reloadRequirements();
      setNotice(
        current ? "Requirement đã được cập nhật. Các test case liên quan cần được rà soát lại." : "Đã lưu requirement.",
      );
    } catch (requestError) {
      setError(toMessage(requestError));
    } finally {
      setSaving(false);
    }
  }
  return {
    content,
    setContent,
    criteria,
    setCriteria,
    current,
    saving,
    error,
    notice,
    save,
    startNew,
    selectRequirement,
  };
}

function useGeneration(token: string, requirement: RequirementRecord | null) {
  const [job, setJob] = useState<GenerationJob | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function generate() {
    if (!requirement) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const submitted = await generateTestCases(token, requirement.id);
      setJob(submitted);
      const finished = await waitForJob(token, submitted);
      setJob(finished);
      setNotice(
        finished.status === "completed"
          ? "AI generation hoàn tất. Mở Review Test Case để rà soát."
          : `Generation thất bại: ${finished.error_code ?? "UNKNOWN"}`,
      );
    } catch (requestError) {
      setError(toMessage(requestError));
    } finally {
      setBusy(false);
    }
  }
  return { job, busy, error, notice, generate };
}

export function RequirementWorkspace({ token, user }: RequirementWorkspaceProps) {
  const moduleState = useModules(token);
  const requirementState = useRequirements(token, moduleState.moduleId);
  const form = useRequirementForm(token, moduleState.moduleId, requirementState.load);
  const generation = useGeneration(token, form.current);
  if (user.role !== USER_ROLE.QA)
    return <StateBlock empty emptyText="Theo SRS, Requirement input và AI generation là luồng của QA." />;
  return (
    <div className="two-column">
      <RequirementPanel
        modules={moduleState.modules}
        moduleId={moduleState.moduleId}
        setModuleId={moduleState.setModuleId}
        loading={moduleState.loading}
        moduleError={moduleState.error}
        requirementState={requirementState}
        form={form}
        generation={generation}
      />
      <JobPanel job={generation.job} notice={generation.notice} error={generation.error} />
    </div>
  );
}

interface RequirementPanelProps {
  modules: ModuleRecord[];
  moduleId: number;
  setModuleId: (id: number) => void;
  loading: boolean;
  moduleError: string;
  requirementState: ReturnType<typeof useRequirements>;
  form: ReturnType<typeof useRequirementForm>;
  generation: ReturnType<typeof useGeneration>;
}

function getRequirementContentError(content: string) {
  if (content.length === 0 || content.trim().length >= 20) {
    return "";
  }

  return "Requirement phải có ít nhất 20 ký tự.";
}

function RequirementPanel(props: RequirementPanelProps) {
  const contentError = getRequirementContentError(props.form.content);

  return (
    <section className="panel">
      <RequirementHeader current={props.form.current} />

      <StateBlock
        loading={props.loading}
        error={props.moduleError || props.requirementState.error || props.form.error}
        empty={!props.loading && props.modules.length === 0}
        emptyText="Chưa có module. Nhờ Manager tạo module trước."
      />

      {!props.loading && props.modules.length > 0 ? (
        <RequirementForm
          modules={props.modules}
          moduleId={props.moduleId}
          setModuleId={props.setModuleId}
          requirementState={props.requirementState}
          form={props.form}
          generation={props.generation}
          contentError={contentError}
        />
      ) : null}
    </section>
  );
}

interface RequirementFormProps {
  modules: ModuleRecord[];
  moduleId: number;
  setModuleId: (id: number) => void;
  requirementState: ReturnType<typeof useRequirements>;
  form: ReturnType<typeof useRequirementForm>;
  generation: ReturnType<typeof useGeneration>;
  contentError: string;
}

function RequirementForm(props: RequirementFormProps) {
  return (
    <form className="stack-form" onSubmit={props.form.save}>
      <RequirementModuleField
        modules={props.modules}
        moduleId={props.moduleId}
        setModuleId={props.setModuleId}
        disabled={false}
      />

      <label>
        Requirement đã lưu
        <select
          disabled={props.requirementState.loading}
          value={props.form.current?.id ?? 0}
          onChange={(event) => {
            const requirementId = Number(event.target.value);

            if (requirementId === 0) {
              props.form.startNew();
              return;
            }

            const selected = props.requirementState.requirements.find(
              (requirement) => requirement.id === requirementId,
            );

            if (selected) props.form.selectRequirement(selected);
          }}
        >
          <option value={0}>+ Tạo Requirement mới</option>
          {props.requirementState.requirements.map((requirement) => (
            <option key={requirement.id} value={requirement.id}>
              {`REQ #${requirement.id} · v${requirement.lock_version} · ${requirement.content.slice(0, 70)}`}
            </option>
          ))}
        </select>
      </label>

      {!props.requirementState.loading && props.requirementState.requirements.length === 0 ? (
        <div className="muted-text">Module này chưa có requirement đã lưu.</div>
      ) : null}

      <RequirementTextFields form={props.form} contentError={props.contentError} />

      <RequirementActions form={props.form} generation={props.generation} contentError={props.contentError} />

      {props.form.notice ? <div className="state state-success">{props.form.notice}</div> : null}
    </form>
  );
}

function RequirementTextFields({
  form,
  contentError,
}: {
  form: ReturnType<typeof useRequirementForm>;
  contentError: string;
}) {
  return (
    <>
      <label>
        Requirement / SRS
        <textarea
          value={form.content}
          onChange={(event) => form.setContent(event.target.value)}
          minLength={20}
          maxLength={50000}
          rows={9}
          required
        />
        <FieldError message={contentError} />
      </label>

      <label>
        Acceptance Criteria
        <textarea
          value={form.criteria}
          onChange={(event) => form.setCriteria(event.target.value)}
          maxLength={20000}
          rows={5}
        />
      </label>
    </>
  );
}

function RequirementActions({
  form,
  generation,
  contentError,
}: {
  form: ReturnType<typeof useRequirementForm>;
  generation: ReturnType<typeof useGeneration>;
  contentError: string;
}) {
  const saveDisabled = form.saving || Boolean(contentError) || form.content.trim().length < 20;

  return (
    <div className="button-row">
      <button className="primary-button" disabled={saveDisabled} type="submit">
        {form.current ? "Cập nhật Requirement" : "Lưu Requirement"}
      </button>

      {form.current ? (
        <button
          className="secondary-button"
          disabled={generation.busy}
          onClick={() => void generation.generate()}
          type="button"
        >
          AI Sinh Test Case
        </button>
      ) : null}
    </div>
  );
}
