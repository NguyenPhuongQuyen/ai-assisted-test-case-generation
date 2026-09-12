import asyncio
import csv
import json
from pathlib import Path

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.common.config import get_settings

BASE = "http://127.0.0.1:8001/api/v1"
MODULE_ID = 4
GOLD_PATH = Path("docs/kiem-thu/gold-set.csv")
RESULT_PATH = Path("docs/kiem-thu/gold-set-results.csv")
EVIDENCE_PATH = Path("docs/kiem-thu/gold-set-evidence.jsonl")


def safe(value):
    if value is None or isinstance(value, (str, int, float, bool, list, dict)):
        return value
    if hasattr(value, "value"):
        return value.value
    return str(value)


def load_evidence():
    data = {}
    if not EVIDENCE_PATH.exists():
        return data

    for line in EVIDENCE_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line)
            data[item["gold_id"]] = item
    return data


def write_results(gold_rows, evidence):
    with RESULT_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "gold_id",
            "requirement_id",
            "job_id",
            "generation_status",
            "generated_test_cases",
            "schema_valid",
            "coverage",
            "technique_match",
            "no_hallucination",
            "evidence_note",
        ])

        for row in gold_rows:
            item = evidence.get(row["gold_id"])

            if not item:
                writer.writerow([row["gold_id"], "", "", "", "", "", "", "", "", ""])
                continue

            cases = item.get("test_cases", [])
            completed = item.get("generation_status") == "completed"
            schema_valid = "PASS" if completed and len(cases) > 0 else "FAIL"
            tc_ids = ", ".join(f"TC#{case['id']}" for case in cases)

            writer.writerow([
                row["gold_id"],
                item.get("requirement_id", ""),
                item.get("job_id", ""),
                item.get("generation_status", ""),
                len(cases),
                schema_valid,
                "",
                "",
                "",
                f"{tc_ids}; error={item.get('error_code') or 'none'}",
            ])


async def load_test_cases(engine, requirement_id):
    async with engine.connect() as conn:
        result = await conn.execute(
            text("""
                SELECT
                    id,
                    summary,
                    preconditions,
                    steps,
                    expected_result,
                    priority,
                    test_techniques,
                    review_note,
                    status
                FROM test_cases
                WHERE requirement_id = :requirement_id
                ORDER BY id
            """),
            {"requirement_id": requirement_id},
        )

        return [
            {key: safe(value) for key, value in row.items()}
            for row in result.mappings().all()
        ]


async def wait_job(client, headers, job):
    current = job

    for _ in range(120):
        if current["status"] in {"completed", "failed"}:
            return current

        await asyncio.sleep(1.5)

        response = await client.get(
            f"{BASE}/generation-jobs/{current['id']}",
            headers=headers,
        )
        response.raise_for_status()
        current = response.json()

    return {
        **current,
        "status": "timeout",
        "error_code": "GOLD_SET_TIMEOUT",
    }


async def main():
    settings = get_settings()
    engine = create_async_engine(settings.database_url)

    with GOLD_PATH.open(encoding="utf-8-sig") as f:
        gold_rows = list(csv.DictReader(f))

    evidence = load_evidence()

    async with httpx.AsyncClient(timeout=30) as client:
        login = await client.post(
            f"{BASE}/auth/login",
            json={
                "email": "qa@example.com",
                "password": settings.demo_user_password,
            },
        )
        login.raise_for_status()

        headers = {
            "Authorization": f"Bearer {login.json()['access_token']}"
        }

        for index, row in enumerate(gold_rows, start=1):
            gold_id = row["gold_id"]

            existing = evidence.get(gold_id)

            if existing and existing.get("generation_status") == "completed":
                print(f"[{index:02}/20] {gold_id} SKIP - da completed")
                continue

            retry_requirement_id = (
                existing.get("requirement_id")
                if existing
                and existing.get("generation_status") == "submit_failed"
                else None
            )

            if retry_requirement_id:
                requirement_id = retry_requirement_id
                print(
                    f"[{index:02}/20] {gold_id} retry REQ #{requirement_id}..."
                )
            else:
                print(f"[{index:02}/20] {gold_id} creating requirement...")

                create = await client.post(
                    f"{BASE}/requirements",
                    headers=headers,
                    json={
                        "module_id": MODULE_ID,
                        "content": row["requirement"],
                        "acceptance_criteria": row["acceptance_criteria"],
                    },
                )

                if create.status_code != 201:
                    item = {
                        "gold_id": gold_id,
                        "requirement_id": None,
                        "job_id": None,
                        "generation_status": "create_failed",
                        "error_code": f"HTTP_{create.status_code}",
                        "test_cases": [],
                    }
                    evidence[gold_id] = item

                    with EVIDENCE_PATH.open("a", encoding="utf-8") as f:
                        f.write(json.dumps(item, ensure_ascii=False) + "\n")

                    write_results(gold_rows, evidence)
                    print(f"        CREATE FAILED HTTP {create.status_code}")
                    continue

                requirement = create.json()
                requirement_id = requirement["id"]

            print(
                f"        REQ #{requirement_id} -> submit AI..."
            )

            submit = await client.post(
                f"{BASE}/requirements/{requirement_id}/test-cases",
                headers=headers,
            )

            if submit.status_code not in {200, 201, 202}:
                item = {
                    "gold_id": gold_id,
                    "requirement_id": requirement_id,
                    "job_id": None,
                    "generation_status": "submit_failed",
                    "error_code": f"HTTP_{submit.status_code}",
                    "test_cases": [],
                }
                evidence[gold_id] = item

                with EVIDENCE_PATH.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")

                write_results(gold_rows, evidence)
                print(f"        SUBMIT FAILED HTTP {submit.status_code}")
                continue

            job = submit.json()

            print(
                f"        JOB #{job['id']} queued - waiting..."
            )

            final_job = await wait_job(client, headers, job)

            cases = await load_test_cases(engine, requirement_id)

            item = {
                "gold_id": gold_id,
                "module": row["module"],
                "requirement": row["requirement"],
                "acceptance_criteria": row["acceptance_criteria"],
                "expected_techniques": row["expected_techniques"],
                "must_cover": row["must_cover"],
                "hallucination_guard": row["hallucination_guard"],
                "requirement_id": requirement_id,
                "job_id": final_job["id"],
                "generation_status": final_job["status"],
                "error_code": final_job.get("error_code"),
                "test_cases": cases,
            }

            evidence[gold_id] = item

            with EVIDENCE_PATH.open("a", encoding="utf-8") as f:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

            write_results(gold_rows, evidence)

            print(
                f"        {final_job['status'].upper()} - "
                f"{len(cases)} test cases"
            )

    await engine.dispose()

    completed = sum(
        1
        for item in evidence.values()
        if item.get("generation_status") == "completed"
    )

    total_cases = sum(
        len(item.get("test_cases", []))
        for item in evidence.values()
    )

    print()
    print("===== GOLD SET RUN COMPLETE =====")
    print("SAMPLES =", len(evidence), "/ 20")
    print("COMPLETED =", completed, "/ 20")
    print("TOTAL GENERATED TEST CASES =", total_cases)
    print("RESULT =", RESULT_PATH)
    print("EVIDENCE =", EVIDENCE_PATH)


if __name__ == "__main__":
    asyncio.run(main())
