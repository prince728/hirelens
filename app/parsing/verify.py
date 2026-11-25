import re
import sys
import unicodedata
from dataclasses import dataclass, field

from app.parsing.extract import extract_text
from app.parsing.parser import parse_resume_text
from app.schemas.resume import Resume


_DASHES = "\u2013\u2014\u2212"  # en dash, em dash, minus sign
_QUOTES = {"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"'}


def normalize(text: str) -> str:
    """Make two strings comparable: ignore case, spacing, line breaks, fancy dashes/quotes."""
    text = unicodedata.normalize("NFKC", text)
    for ch in _DASHES:
        text = text.replace(ch, "-")
    for fancy, plain in _QUOTES.items():
        text = text.replace(fancy, plain)
    text = re.sub(r"\s+", " ", text) 
    return text.strip().lower()


VERIFIED = "verified"
UNVERIFIED = "unverified"    
NO_EVIDENCE = "no_evidence"    


@dataclass
class ItemResult:
    kind: str    
    label: str      
    status: str
    evidence: str


@dataclass
class VerificationReport:
    results: list[ItemResult] = field(default_factory=list)

    def of(self, kind: str, status: str) -> list[ItemResult]:
        return [r for r in self.results if r.kind == kind and r.status == status]

    def count(self, status: str, kind: str | None = None) -> int:
        return sum(
            1 for r in self.results
            if r.status == status and (kind is None or r.kind == kind)
        )

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def verified_rate(self) -> float:
        """Share of items WITH evidence whose evidence was found in the text."""
        with_evidence = self.count(VERIFIED) + self.count(UNVERIFIED)
        return self.count(VERIFIED) / with_evidence if with_evidence else 1.0


def _check(evidence: str, normalized_text: str) -> str:
    evidence = (evidence or "").strip()
    if not evidence:
        return NO_EVIDENCE
    return VERIFIED if normalize(evidence) in normalized_text else UNVERIFIED


def verify_resume(resume: Resume, source_text: str) -> VerificationReport:
    text = normalize(source_text)
    report = VerificationReport()

    for s in resume.skills:
        report.results.append(ItemResult("skill", s.name, _check(s.evidence, text), s.evidence))

    for p in resume.projects:
        report.results.append(
            ItemResult("project", p.name or "(unnamed)", _check(p.evidence, text), p.evidence)
        )

    for e in resume.experience:
        label = " at ".join(x for x in (e.title, e.company) if x) or "(unnamed)"
        report.results.append(ItemResult("experience", label, _check(e.evidence, text), e.evidence))

    return report



_INJECTION_PATTERNS = [
    r"ignore (all |any |the )?(previous|prior|above|earlier) (instructions|prompts?|rules)",
    r"disregard (all |any |the )?(previous|prior|above|earlier)",
    r"forget (all |any |the )?(previous|prior|above|earlier)",
    r"(reveal|show|print) (your |the )?(system )?prompt",
    r"you are now",
    r"new instructions?:",
    r"(rate|score|rank|grade) (this|the) (candidate|resume|applicant)",
    r"(give|assign) (this|the) (candidate|resume|applicant)",
    r"(hire|select|shortlist) this (candidate|applicant)",
    r"\b10\s*/\s*10\b",
    r"perfect (match|candidate|score)",
]


def scan_for_injection(source_text: str) -> list[str]:
    """Return the suspicious phrases found in the text (empty list = nothing found).

    This only sees text that was extracted. Hidden text (for example white-on-white)
    still shows up here, because extraction reads it too, which is the point.
    """
    text = normalize(source_text)
    hits = []
    for pattern in _INJECTION_PATTERNS:
        for m in re.finditer(pattern, text):
            hits.append(m.group(0))
    return hits


def print_report(report: VerificationReport) -> None:
    for kind in ("skill", "project", "experience"):
        items = [r for r in report.results if r.kind == kind]
        if not items:
            continue
        print(
            f"{kind:<11} total={len(items):<3} "
            f"verified={report.count(VERIFIED, kind):<3} "
            f"unverified={report.count(UNVERIFIED, kind):<3} "
            f"no_evidence={report.count(NO_EVIDENCE, kind)}"
        )

    print(f"\nEvidence found in resume: {report.verified_rate:.0%} of items that gave evidence")

    bad = [r for r in report.results if r.status == UNVERIFIED]
    if bad:
        print("\nUNVERIFIED (possible hallucination):")
        for r in bad:
            print(f"  [{r.kind}] {r.label}: {r.evidence[:100]}")

    claimed = [r for r in report.results if r.status == NO_EVIDENCE]
    if claimed:
        print("\nClaimed only (no evidence given): " + ", ".join(r.label for r in claimed))


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/Prince_Gupta_Resume.pdf"
    text = extract_text(path)

    flags = scan_for_injection(text)
    print("Injection scan:", f"FLAGGED -> {flags}" if flags else "clean")

    resume = parse_resume_text(text)
    print("\n--- Verification ---")
    print_report(verify_resume(resume, text))

    # Self-test: plant one fake evidence string and make sure the check catches it.
    if resume.skills:
        tampered = resume.model_copy(deep=True)
        tampered.skills[0].evidence = "Led a team of 50 engineers at Google."
        caught = verify_resume(tampered, text).of("skill", UNVERIFIED)
        print("\nSelf-test (fake evidence planted):", "CAUGHT" if caught else "MISSED - check normalize()")