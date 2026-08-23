import type { CoverageResponse, ModuleListResponse, ModuleRecord } from "@/types/api";
import { apiRequest } from "./api";

export function listModules(token: string): Promise<ModuleListResponse> {
  return apiRequest<ModuleListResponse>("/modules?page=1&pageSize=100", {}, token);
}

export function createModule(token: string, name: string, parentId: number | null): Promise<ModuleRecord> {
  return apiRequest<ModuleRecord>(
    "/modules",
    { method: "POST", body: JSON.stringify({ name, parent_id: parentId }) },
    token,
  );
}

export function updateModule(token: string, moduleId: number, name: string): Promise<ModuleRecord> {
  return apiRequest<ModuleRecord>(`/modules/${moduleId}`, { method: "PATCH", body: JSON.stringify({ name }) }, token);
}

export function getCoverage(token: string, moduleId: number): Promise<CoverageResponse> {
  return apiRequest<CoverageResponse>(`/modules/${moduleId}/coverage`, {}, token);
}

export function updateTags(token: string, moduleId: number, testCaseId: number, tags: string[]) {
  return apiRequest<{ id: number; module_id: number; tags: string[] }>(
    `/modules/${moduleId}/test-cases/${testCaseId}/tags`,
    { method: "PATCH", body: JSON.stringify({ tags }) },
    token,
  );
}
