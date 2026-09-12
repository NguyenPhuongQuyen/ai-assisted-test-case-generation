import type { RequirementRecord } from "@/types/api";
import { apiRequest } from "./api";

interface RequirementListResponse {
  data: RequirementRecord[];
  page: number;
  page_size: number;
  total: number;
}

export function listRequirements(token: string, moduleId: number): Promise<RequirementListResponse> {
  return apiRequest<RequirementListResponse>(
    `/requirements?module_id=${moduleId}&page=1&page_size=100`,
    { method: "GET" },
    token,
  );
}

export function createRequirement(
  token: string,
  moduleId: number,
  content: string,
  acceptanceCriteria: string,
): Promise<RequirementRecord> {
  return apiRequest<RequirementRecord>(
    "/requirements",
    {
      method: "POST",
      body: JSON.stringify({
        module_id: moduleId,
        content,
        acceptance_criteria: acceptanceCriteria || null,
      }),
    },
    token,
  );
}

export function updateRequirement(
  token: string,
  requirement: RequirementRecord,
  content: string,
  acceptanceCriteria: string,
): Promise<RequirementRecord> {
  return apiRequest<RequirementRecord>(
    `/requirements/${requirement.id}`,
    {
      method: "PATCH",
      body: JSON.stringify({
        lock_version: requirement.lock_version,
        content,
        acceptance_criteria: acceptanceCriteria || null,
      }),
    },
    token,
  );
}
