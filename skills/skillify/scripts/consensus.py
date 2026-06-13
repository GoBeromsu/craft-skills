#!/usr/bin/env python3
"""consensus.py — vendored multi-model consensus channel for skillify.

Fans out a skill-under-eval to codex, gemini, and claude, collects
structured verdicts (APPROVE / REVISE + findings), writes per-model
artifacts and a synthesized consensus receipt.

Usage:
    python3 consensus.py --skill <skill-dir> [--round N] \\
                         [--prior <receipt-path>] [--providers codex,gemini,claude]

Design:
    - Calls each model CLI DIRECTLY via subprocess. Never invokes the OMC binary.
    - Graceful degradation: missing or erroring CLIs are recorded and skipped.
    - A run with fewer than all requested models live is flagged "degraded".
    - Headless-safe: no interactive prompts; Bash-callable from a subagent.
"""
from __future__ import annotations

import argparse
import datetime
import shutil
import subprocess
import sys
from pathlib import Path

# --------------------------------------------------------------------------- #
# Provider configuration
# --------------------------------------------------------------------------- #

PROVIDER_DEFAULTS = ["codex", "gemini", "claude"]

# How each provider CLI is invoked.
# prompt_via="arg"   — prompt appended as the last positional argument.
# prompt_via="stdin" — prompt sent via stdin.
PROVIDER_CONFIG: dict[str, dict] = {
    "codex": {
        # --ignore-user-config: prevents loading ~/.codex/config.toml which may
        # have [agents] max_threads set — incompatible with the v2 multi-agent
        # runtime (causes "thread/start failed: agents.max_threads cannot be set
        # when the multi-agent runtime is v2").
        # --dangerously-bypass-approvals-and-sandbox: required for headless/non-
        # interactive execution (no TTY to approve tool calls).
        "cmd": ["codex", "exec", "--ignore-user-config",
                "--dangerously-bypass-approvals-and-sandbox"],
        "prompt_via": "arg",
        "timeout": 120,
    },
    "gemini": {
        "cmd": ["gemini"],
        "prompt_via": "stdin",
        "timeout": 120,
    },
    "claude": {
        "cmd": ["claude", "-p"],
        "prompt_via": "arg",
        "timeout": 120,
    },
}

# Role-scoped prompts per provider:
#   codex  → architecture / routing / correctness
#   gemini → trigger-phrase UX / docs clarity
#   claude → anatomy / contract conformance
ROLE_PROMPTS: dict[str, str] = {
    "codex": (
        "You are reviewing a skill package for architecture, routing correctness, "
        "and implementation quality.\n\n"
        "Evaluate whether the skill is architecturally sound, correctly uses "
        "real trigger phrases, and is free from structural or logic errors.\n\n"
        "Respond with EXACTLY this format:\n"
        "VERDICT: APPROVE\n"
        "or\n"
        "VERDICT: REVISE\n"
        "FINDINGS:\n"
        "- <finding>\n\n"
        "SKILL.md content:\n{skill_text}"
    ),
    "gemini": (
        "You are reviewing a skill package for trigger-phrase UX and documentation clarity.\n\n"
        "Evaluate whether the description is a real user trigger phrase (not a capability "
        "blurb), and whether the documentation is clear, well-structured, and jargon-free.\n\n"
        "Respond with EXACTLY this format:\n"
        "VERDICT: APPROVE\n"
        "or\n"
        "VERDICT: REVISE\n"
        "FINDINGS:\n"
        "- <finding>\n\n"
        "SKILL.md content:\n{skill_text}"
    ),
    "claude": (
        "You are reviewing a skill package for anatomy conformance and contract compliance.\n\n"
        "The frontmatter must have exactly 5 keys: name, description, version, "
        "allowed-tools (YAML list), and compatibility (non-empty, ≤500 chars). "
        "CHANGELOG.md presence is enforced by Layer-1 (validate-skill-format.py) before this "
        "stage runs — do not re-check it; you cannot see it from here. "
        "The SKILL.md body must contain no history-narrative pollution "
        "(no '## Change Log' section, no self-narration of the skill's own evolution).\n\n"
        "Respond with EXACTLY this format:\n"
        "VERDICT: APPROVE\n"
        "or\n"
        "VERDICT: REVISE\n"
        "FINDINGS:\n"
        "- <finding>\n\n"
        "SKILL.md content:\n{skill_text}"
    ),
}


# --------------------------------------------------------------------------- #
# Core functions
# --------------------------------------------------------------------------- #

def build_prompt(provider: str, skill_text: str, prior_text: str | None) -> str:
    """Build a role-scoped evaluation prompt for the given provider."""
    base = ROLE_PROMPTS[provider].format(skill_text=skill_text)
    if prior_text:
        base += (
            "\n\n---\n"
            "PRIOR ROUND FINDINGS (for rebuttal context — defend or concede each point):\n"
            + prior_text
        )
    return base


def check_provider_available(provider: str) -> bool:
    """Return True if the provider CLI binary is on PATH."""
    binary = PROVIDER_CONFIG[provider]["cmd"][0]
    return shutil.which(binary) is not None


def invoke_provider(provider: str, prompt: str) -> tuple[str | None, str | None]:
    """Invoke a provider CLI with the given prompt.

    Returns ``(output_text, error_message)``.
    On success ``error_message`` is None.
    On failure ``output_text`` is None and ``error_message`` describes the problem.
    """
    config = PROVIDER_CONFIG[provider]
    cmd = list(config["cmd"])
    timeout: int = config["timeout"]

    if config["prompt_via"] == "arg":
        cmd.append(prompt)
        # Explicitly close stdin so CLIs (e.g. codex) don't detect a piped
        # stdin and try to read an additional prompt from it.
        stdin_kwarg: dict = {"stdin": subprocess.DEVNULL}
    else:
        stdin_kwarg = {"input": prompt}

    try:
        result = subprocess.run(
            cmd,
            **stdin_kwarg,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            err = result.stderr.strip() or f"exit code {result.returncode}"
            return None, f"CLI error: {err}"
        return result.stdout.strip(), None
    except FileNotFoundError:
        return None, f"CLI binary not found: {cmd[0]!r}"
    except subprocess.TimeoutExpired:
        return None, f"CLI timed out after {timeout}s"
    except Exception as exc:  # noqa: BLE001
        return None, f"Unexpected error invoking {provider}: {exc}"


def write_artifact(evals_dir: Path, provider: str, round_n: int, content: str) -> Path:
    """Write a per-model eval artifact and return its path."""
    evals_dir.mkdir(parents=True, exist_ok=True)
    out = evals_dir / f"{provider}-r{round_n}.md"
    out.write_text(content, encoding="utf-8")
    return out


def _is_approve(verdict_text: str) -> bool:
    """Return True if the verdict text signals APPROVE."""
    upper = verdict_text.upper()
    return "VERDICT: APPROVE" in upper


def synthesize_receipt(
    skill_name: str,
    round_n: int,
    verdicts: dict[str, str],
    errors: dict[str, str],
    providers: list[str],
    today: str,
) -> str:
    """Build the synthesized consensus receipt text."""
    live = [p for p in providers if p not in errors]
    degraded = len(live) < len(providers)

    all_approve = bool(verdicts) and all(_is_approve(v) for v in verdicts.values())

    if degraded:
        status = "degraded"
    elif all_approve:
        status = "CONVERGED"
    else:
        status = "DIVERGED"

    lines = [
        f"# Consensus Receipt — {skill_name} — round {round_n} — {today}",
        "",
        f"status: {status}",
        f"providers_requested: {', '.join(providers)}",
        f"providers_live: {', '.join(live) if live else '(none)'}",
        "",
    ]

    if errors:
        lines += ["## Degraded Providers", ""]
        for p, err in errors.items():
            lines.append(f"- **{p}**: {err}")
        lines.append("")

    for provider, verdict in verdicts.items():
        lines += [f"## {provider} verdict", "", verdict, ""]

    if all_approve and not degraded:
        lines += [
            "## Result",
            "",
            "CONVERGED — all models APPROVE. Gate passes.",
            "",
        ]
    elif all_approve and degraded:
        lines += [
            "## Result",
            "",
            f"Partial convergence (degraded: {len(live)}/{len(providers)} models live). "
            "All live models APPROVE. Re-run with all providers available to confirm.",
            "",
        ]
    elif not all_approve and verdicts:
        lines += [
            "## Residual Conflict",
            "",
            "Models did not converge. The disagreement above is submitted to the user.",
            "Please review findings, revise the skill, and re-run consensus.",
            "",
        ]
    else:
        # No verdicts at all (fully degraded)
        lines += [
            "## Result",
            "",
            "No providers were reachable. Nothing to evaluate. Check provider CLIs.",
            "",
        ]

    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def main_with_args(
    skill: str,
    round_n: int = 1,
    prior: str | None = None,
    providers: list[str] | None = None,
) -> int:
    """Core consensus logic, callable directly (for tests and programmatic use).

    Returns:
        0  — all providers live and converged (or no violations).
        1  — hard error (e.g. SKILL.md missing).
        2  — degraded: fewer than all requested providers were reachable.
    """
    if providers is None:
        providers = list(PROVIDER_DEFAULTS)

    skill_dir = Path(skill).resolve()
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        print(f"ERROR: SKILL.md not found at {skill_md}", file=sys.stderr)
        return 1

    skill_text = skill_md.read_text(encoding="utf-8")
    skill_name = skill_dir.name

    prior_text: str | None = None
    if prior:
        prior_path = Path(prior)
        if prior_path.exists():
            prior_text = prior_path.read_text(encoding="utf-8")
        else:
            print(f"WARNING: prior receipt not found: {prior}", file=sys.stderr)

    today = datetime.date.today().isoformat()
    evals_dir = skill_dir / "evals"

    verdicts: dict[str, str] = {}
    errors: dict[str, str] = {}

    for provider in providers:
        if provider not in PROVIDER_CONFIG:
            errors[provider] = f"unknown provider {provider!r}"
            print(f"  [{provider}] SKIP: {errors[provider]}", file=sys.stderr)
            continue

        if not check_provider_available(provider):
            errors[provider] = (
                f"CLI binary not found on PATH: "
                f"{PROVIDER_CONFIG[provider]['cmd'][0]!r}"
            )
            print(f"  [{provider}] SKIP: {errors[provider]}", file=sys.stderr)
            continue

        print(f"  [{provider}] invoking...", file=sys.stderr)
        prompt = build_prompt(provider, skill_text, prior_text)
        output, err = invoke_provider(provider, prompt)

        if err:
            errors[provider] = err
            print(f"  [{provider}] ERROR: {err}", file=sys.stderr)
        else:
            verdicts[provider] = output or ""
            artifact = write_artifact(evals_dir, provider, round_n, output or "")
            print(f"  [{provider}] verdict written → {artifact}", file=sys.stderr)

    receipt_text = synthesize_receipt(
        skill_name=skill_name,
        round_n=round_n,
        verdicts=verdicts,
        errors=errors,
        providers=providers,
        today=today,
    )

    evals_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = evals_dir / f"consensus-{skill_name}-{today}.md"
    receipt_path.write_text(receipt_text, encoding="utf-8")
    print(f"\nconsensus receipt → {receipt_path}", file=sys.stderr)

    live_count = len(providers) - len(errors)
    if live_count < len(providers):
        print(
            f"WARNING: degraded run — {live_count}/{len(providers)} providers live.",
            file=sys.stderr,
        )
        return 2  # degraded; receipt written, but not a hard failure

    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Vendored multi-model consensus channel for skillify.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--skill", required=True,
        help="Path to the skill directory under evaluation.",
    )
    ap.add_argument(
        "--round", type=int, default=1, dest="round_n", metavar="N",
        help="Round number (default: 1).",
    )
    ap.add_argument(
        "--prior", default=None, metavar="RECEIPT_PATH",
        help="Path to a prior round consensus receipt for rebuttal context (optional).",
    )
    ap.add_argument(
        "--providers", default=",".join(PROVIDER_DEFAULTS),
        help=(
            f"Comma-separated list of providers to consult "
            f"(default: {','.join(PROVIDER_DEFAULTS)})."
        ),
    )
    args = ap.parse_args()

    providers = [p.strip() for p in args.providers.split(",") if p.strip()]
    return main_with_args(
        skill=args.skill,
        round_n=args.round_n,
        prior=args.prior,
        providers=providers,
    )


if __name__ == "__main__":
    raise SystemExit(main())
