"use client";

// Source assistance: OpenAI ChatGPT, 2026-08-25 (AI-05).
import { USER_ROLE } from "@/constants/user-role";
import type { CoverageResponse, User } from "@/types/api";

export function ManagementHeader() {
  return (
    <div className="panel-heading">
      <div>
        <div className="eyebrow">NC-06</div>
        <h3>Tổ chức theo Module</h3>
      </div>
    </div>
  );
}

export function CoverageHeader() {
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

export function CoverageActionButtons(props: CoverageActionButtonsProps) {
  const exportDisabled = props.busy || !props.moduleId || props.user.role === USER_ROLE.ADMIN;

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

export function CoverageMessages({ action }: { action: { error: string; notice: string } }) {
  return (
    <>
      {action.error ? <div className="state state-error">{action.error}</div> : null}

      {action.notice ? <div className="state state-success">{action.notice}</div> : null}
    </>
  );
}

export function CoverageCard({ coverage }: { coverage: CoverageResponse }) {
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
