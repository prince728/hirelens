"""Consistency eval: parse the same resume several times and measure how much the output varies.

Usage (from the project root):
    uv run python -m eval.consistency data/Prince_Gupta_Resume.pdf 10

It reports:
  - how many runs failed or came back empty
  - how many skills each run found
  - how similar the skill lists are between runs (Jaccard, 1.0 = identical)
  - which skills appear in every run and which come and go
  - how much of the evidence was verified in each run

Only skill names and counts are saved (no contact details), so the result file is safe to commit.
"""

import json
import sys
import time
from collections import Counter
from datetime import datetime
from itertools import combinations
from pathlib import Path

from app.parsing.extract import extract_text
from app.parsing.parser import parse_resume_text
from app.parsing.verify import UNVERIFIED, VERIFIED, verify_resume
from app.schemas.resume import Resume

PAUSE_SECONDS = 2
RESULTS_DIR = Path("eval/results")


def is_empty(resume: Resume) -> bool:
    return not (resume.skills or resume.projects or resume.experience or resume.education)


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def run_once(text: str) -> dict:
    """One parse. Never raises: failures are recorded so one bad run doesn't stop the eval."""
    start = time.time()
    try:
        resume = parse_resume_text(text)
    except Exception as e: 
        return {"status": "error", "error": f"{type(e).__name__}: {str(e)[:200]}", "seconds": time.time() - start}

    seconds = time.time() - start
    if is_empty(resume):
        return {"status": "empty", "seconds": seconds}

    report = verify_resume(resume, text)
    return {
        "status": "ok",
        "seconds": seconds,
        "skills": sorted({s.name.strip().lower() for s in resume.skills}),
        "projects": len(resume.projects),
        "experience": len(resume.experience),
        "verified": report.count(VERIFIED),
        "unverified": report.count(UNVERIFIED),
    }


def summarize(runs: list[dict]) -> dict:
    ok = [r for r in runs if r["status"] == "ok"]
    summary = {
        "total_runs": len(runs),
        "ok": len(ok),
        "empty": sum(r["status"] == "empty" for r in runs),
        "errors": sum(r["status"] == "error" for r in runs),
    }
    if not ok:
        return summary

    counts = [len(r["skills"]) for r in ok]
    summary["skills_per_run"] = {"min": min(counts), "max": max(counts), "mean": round(sum(counts) / len(counts), 1)}

    sets = [set(r["skills"]) for r in ok]
    if len(sets) > 1:
        sims = [jaccard(a, b) for a, b in combinations(sets, 2)]
        summary["mean_skill_similarity"] = round(sum(sims) / len(sims), 3)
    else:
        summary["mean_skill_similarity"] = 1.0

    freq = Counter(skill for s in sets for skill in s)
    summary["stable_skills"] = sorted(k for k, v in freq.items() if v == len(ok))
    summary["unstable_skills"] = {k: f"{v}/{len(ok)}" for k, v in sorted(freq.items()) if v < len(ok)}

    summary["total_unverified"] = sum(r["unverified"] for r in ok)
    summary["mean_seconds"] = round(sum(r["seconds"] for r in runs) / len(runs), 1)
    return summary


def print_summary(path: str, summary: dict, runs: list[dict]) -> None:
    print(f"\nConsistency eval: {path}")
    print(f"Runs: {summary['total_runs']}   ok: {summary['ok']}   empty: {summary['empty']}   errors: {summary['errors']}")

    print("\nPer run:")
    for i, r in enumerate(runs, 1):
        if r["status"] == "ok":
            print(f"  {i:>2}. ok     skills={len(r['skills']):<3} verified={r['verified']:<3} unverified={r['unverified']:<3} {r['seconds']:.1f}s")
        elif r["status"] == "empty":
            print(f"  {i:>2}. EMPTY  (valid but nothing extracted)")
        else:
            print(f"  {i:>2}. ERROR  {r['error']}")

    if summary["ok"] == 0:
        print("\nNo successful runs to compare.")
        return

    spc = summary["skills_per_run"]
    print(f"\nSkills per run: min {spc['min']}, max {spc['max']}, mean {spc['mean']}")
    print(f"Mean skill-list similarity between runs: {summary['mean_skill_similarity']} (1.0 = identical)")
    print(f"Skills found in every run: {len(summary['stable_skills'])}")
    if summary["unstable_skills"]:
        print("Skills that come and go:")
        for name, seen in summary["unstable_skills"].items():
            print(f"  {name}: {seen}")
    print(f"Unverified evidence across all runs: {summary['total_unverified']}")


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else "data/Prince_Gupta_Resume.pdf"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    text = extract_text(path)
    runs = []
    for i in range(n):
        print(f"run {i + 1}/{n}...", flush=True)
        runs.append(run_once(text))
        if i < n - 1:
            time.sleep(PAUSE_SECONDS)

    summary = summarize(runs)
    print_summary(path, summary, runs)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"consistency_{datetime.now():%Y%m%d_%H%M%S}.json"
    out.write_text(json.dumps({"file": Path(path).name, "summary": summary, "runs": runs}, indent=2))
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()
