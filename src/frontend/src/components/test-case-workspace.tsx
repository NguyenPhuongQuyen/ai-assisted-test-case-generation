"use client";

// Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).
import { useCallback, useEffect, useState } from "react";

import { ApiError } from "@/services/api";
import { listTestCases } from "@/services/testcases";
import type { TestCaseRecord, TestCaseStatus, User } from "@/types/api";
import { TestCaseEditor } from "./test-case-editor";
import { TestCaseInsights } from "./test-case-insights";
import { TestCaseList } from "./test-case-list";

interface TestCaseWorkspaceProps {
  token: string;
  user: User;
}

function errorText(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  return error instanceof Error ? error.message : "Không thể tải test case.";
}

export function TestCaseWorkspace({ token, user }: TestCaseWorkspaceProps) {
  const [items, setItems] = useState<TestCaseRecord[]>([]);
  const [selected, setSelected] = useState<TestCaseRecord | null>(null);
  const [status, setStatus] = useState<"" | TestCaseStatus>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await listTestCases(token, status || undefined);
      setItems(response.data);
      setSelected((current) => response.data.find((item) => item.id === current?.id) ?? response.data[0] ?? null);
    } catch (requestError) {
      setError(errorText(requestError));
    } finally {
      setLoading(false);
    }
  }, [status, token]);

  useEffect(() => {
    queueMicrotask(() => void load());
  }, [load]);

  function replace(updated: TestCaseRecord) {
    setSelected(updated);
    setItems((current) => current.map((item) => (item.id === updated.id ? updated : item)));
  }

  return (
    <div className="review-layout">
      <TestCaseList
        items={items}
        selectedId={selected?.id}
        loading={loading}
        error={error}
        status={status}
        onStatusChange={setStatus}
        onReload={() => void load()}
        onSelect={setSelected}
      />
      <div className="review-detail">
        <TestCaseEditor token={token} user={user} record={selected} onChanged={replace} />
        <TestCaseInsights token={token} user={user} record={selected} onChanged={replace} onReload={load} />
      </div>
    </div>
  );
}
