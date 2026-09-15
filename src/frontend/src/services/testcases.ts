// Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).

import type {
  DuplicateCandidateListResponse,
  DuplicateMergeResponse,
  GenerationJob,
  Priority,
  TestCaseListResponse,
  TestCaseRecord,
  TestCaseStatus,
  TestCaseVersionListResponse,
  VersionCompareResponse,
} from "@/types/api";
import { apiRequest, downloadRequest } from "./api";

export function generateTestCases(token: string, requirementId: number): Promise<GenerationJob> {
  return apiRequest<GenerationJob>(`/requirements/${requirementId}/test-cases`, { method: "POST" }, token);
}

export function createManualTestCase(
  token: string,
  requirementId: number,
  input: {
    summary: string;
    preconditions: string[];
    steps: string[];
    expectedResult: string;
    priority: Priority;
    testTechniques: string[];
  },
): Promise<TestCaseRecord> {
  return apiRequest<TestCaseRecord>(
    `/requirements/${requirementId}/test-cases/manual`,
    {
      method: "POST",
      body: JSON.stringify({
        summary: input.summary,
        preconditions: input.preconditions,
        steps: input.steps,
        expected_result: input.expectedResult,
        priority: input.priority,
        test_techniques: input.testTechniques,
      }),
    },
    token,
  );
}

export function getGenerationJob(token: string, jobId: number): Promise<GenerationJob> {
  return apiRequest<GenerationJob>(`/generation-jobs/${jobId}`, {}, token);
}

export function listTestCases(token: string, status?: TestCaseStatus): Promise<TestCaseListResponse> {
  const query = status ? `?status=${status}&page=1&pageSize=100` : "?page=1&pageSize=100";
  return apiRequest<TestCaseListResponse>(`/test-cases${query}`, {}, token);
}

export function updateTestCase(
  token: string,
  record: TestCaseRecord,
  input: {
    summary: string;
    preconditions: string[];
    steps: string[];
    expectedResult: string;
    priority: Priority;
    testTechniques: string[];
    reviewNote: string;
  },
) {
  return apiRequest<TestCaseRecord>(
    `/test-cases/${record.id}`,
    {
      method: "PATCH",
      body: JSON.stringify({
        lock_version: record.lock_version,
        summary: input.summary,
        preconditions: input.preconditions,
        steps: input.steps,
        expected_result: input.expectedResult,
        priority: input.priority,
        test_techniques: input.testTechniques,
        review_note: input.reviewNote || null,
      }),
    },
    token,
  );
}

export function transitionTestCase(
  token: string,
  record: TestCaseRecord,
  action: "review" | "approve" | "request-fix" | "reject",
  reviewNote?: string,
) {
  const body =
    action === "review"
      ? { lock_version: record.lock_version }
      : {
          lock_version: record.lock_version,
          review_note: reviewNote || null,
        };
  return apiRequest<TestCaseRecord>(
    `/test-cases/${record.id}/${action}`,
    { method: "POST", body: JSON.stringify(body) },
    token,
  );
}

export function listDuplicates(token: string, testCaseId: number): Promise<DuplicateCandidateListResponse> {
  return apiRequest<DuplicateCandidateListResponse>(`/test-cases/${testCaseId}/duplicate-candidates`, {}, token);
}

export function mergeDuplicate(
  token: string,
  record: TestCaseRecord,
  sourceTestCaseId: number,
): Promise<DuplicateMergeResponse> {
  return apiRequest<DuplicateMergeResponse>(
    `/test-cases/${record.id}/merge-duplicate`,
    {
      method: "POST",
      body: JSON.stringify({
        lock_version: record.lock_version,
        source_test_case_id: sourceTestCaseId,
      }),
    },
    token,
  );
}

export function listVersions(token: string, testCaseId: number): Promise<TestCaseVersionListResponse> {
  return apiRequest<TestCaseVersionListResponse>(`/test-cases/${testCaseId}/versions?page=1&pageSize=100`, {}, token);
}

export function compareVersions(token: string, testCaseId: number, fromVersion: number, toVersion: number) {
  return apiRequest<VersionCompareResponse>(
    `/test-cases/${testCaseId}/versions/compare?fromVersion=${fromVersion}&toVersion=${toVersion}`,
    {},
    token,
  );
}

export function restoreVersion(token: string, record: TestCaseRecord, versionNumber: number) {
  return apiRequest<TestCaseRecord>(
    `/test-cases/${record.id}/versions/${versionNumber}/restore`,
    { method: "POST", body: JSON.stringify({ lock_version: record.lock_version }) },
    token,
  );
}

export function exportTestCases(token: string, moduleId: number, format: "csv" | "xlsx") {
  return downloadRequest(`/test-cases/export?module_id=${moduleId}&format=${format}`, token);
}
