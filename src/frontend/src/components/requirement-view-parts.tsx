"use client";

// Source assistance: OpenAI ChatGPT, 2026-08-25 (AI-05).
import type { GenerationJob, ModuleRecord, RequirementRecord } from "@/types/api";
import { StateBlock } from "./state-block";

export function RequirementHeader({ current }: { current: RequirementRecord | null }) {
  return (
    <div className="panel-heading">
      <div>
        <div className="eyebrow">NC-01 · YC-01</div>
        <h3>Nhập đặc tả yêu cầu</h3>
      </div>

      {current ? (
        <span className="status-badge">
          REQ #{current.id} · v{current.lock_version}
        </span>
      ) : null}
    </div>
  );
}

interface RequirementModuleFieldProps {
  modules: ModuleRecord[];
  moduleId: number;
  setModuleId: (id: number) => void;
  disabled: boolean;
}

export function RequirementModuleField(props: RequirementModuleFieldProps) {
  return (
    <label>
      Module
      <select
        value={props.moduleId}
        onChange={(event) => props.setModuleId(Number(event.target.value))}
        disabled={props.disabled}
      >
        {props.modules.map((module) => (
          <option key={module.id} value={module.id}>
            {module.name}
          </option>
        ))}
      </select>
    </label>
  );
}

export function JobPanel({ job, notice, error }: { job: GenerationJob | null; notice: string; error: string }) {
  return (
    <section className="panel muted-panel">
      <div className="eyebrow">NC-02 · NC-03</div>
      <h3>Generation Job</h3>
      {!job ? (
        <StateBlock empty emptyText="Chưa có generation job trong phiên làm việc này." />
      ) : (
        <div className="job-card">
          <div>
            <strong>Job #{job.id}</strong>
          </div>
          <div>Requirement: #{job.requirement_id}</div>
          <div>
            Trạng thái: <span className={`status-badge status-${job.status}`}>{job.status}</span>
          </div>
          {job.error_code ? <div className="state state-error">{job.error_code}</div> : null}
        </div>
      )}
      {error ? <div className="state state-error">{error}</div> : null}
      {notice ? <div className="state state-success">{notice}</div> : null}
      <div className="help-box">
        <strong>Luồng đúng SRS</strong>
        <p>AI chỉ sinh bản DRAFT. Test case phải qua review/approve trước khi export.</p>
      </div>
    </section>
  );
}
