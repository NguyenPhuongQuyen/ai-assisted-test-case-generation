import type { RequirementRecord } from "@/types/api";
import { apiRequest } from "./api";

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
