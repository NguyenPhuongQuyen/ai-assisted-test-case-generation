"use client";

// Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).
import type { TestCaseRecord, TestCaseStatus } from "@/types/api";
import { StateBlock } from "./state-block";

interface TestCaseListProps {
  items: TestCaseRecord[];
  selectedId?: number;
  loading: boolean;
  error: string;
  status: "" | TestCaseStatus;
  onStatusChange: (status: "" | TestCaseStatus) => void;
  onReload: () => void;
  onSelect: (record: TestCaseRecord) => void;
}

const statuses: TestCaseStatus[] = ["draft", "in_review", "needs_fix", "approved", "rejected", "exported"];

export function TestCaseList(props: TestCaseListProps) {
  return (
    <section className="panel list-panel">
      <div className="panel-heading">
        <div>
          <div className="eyebrow">NC-04 · BR-01</div>
          <h3>Test Case List</h3>
        </div>
        <button className="ghost-button compact" onClick={props.onReload} type="button">
          Tải lại
        </button>
      </div>
      <label>
        Lọc trạng thái
        <select
          value={props.status}
          onChange={(event) => props.onStatusChange(event.target.value as "" | TestCaseStatus)}
        >
          <option value="">Tất cả</option>
          {statuses.map((status) => (
            <option key={status} value={status}>
              {status}
            </option>
          ))}
        </select>
      </label>
      <StateBlock
        loading={props.loading}
        error={props.error}
        empty={!props.loading && props.items.length === 0}
        emptyText="Không có test case phù hợp bộ lọc."
      />
      <div className="case-list">
        {props.items.map((record) => (
          <button
            className={props.selectedId === record.id ? "case-card selected" : "case-card"}
            key={record.id}
            onClick={() => props.onSelect(record)}
            type="button"
          >
            <span className={`priority priority-${record.priority}`}>{record.priority}</span>
            <strong>TC #{record.id}</strong>
            <span className="case-summary">{record.summary}</span>
            <span className={`status-badge status-${record.status}`}>{record.status}</span>
          </button>
        ))}
      </div>
    </section>
  );
}
