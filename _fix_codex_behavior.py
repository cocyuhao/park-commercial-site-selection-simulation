"""Fix Codex behavioral quality: marketplace manifest + global AGENTS.md rules + personality."""
from __future__ import annotations
import json, pathlib, os

HOME = pathlib.Path(os.environ["USERPROFILE"])
CODEX = HOME / ".codex"

# ── 1. Fix community marketplace manifest ────────────────────────────────────
agents_dir = CODEX / ".tmp" / "community-marketplace" / ".agents" / "plugins"
agents_dir.mkdir(parents=True, exist_ok=True)
manifest = {
    "name": "community",
    "interface": {"displayName": "Community"},
    "plugins": [
        {
            "name": "chrome-devtools",
            "source": {"source": "local", "path": "./plugins/chrome-devtools"},
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": "Engineering",
        },
        {
            "name": "context-pack",
            "source": {"source": "local", "path": "./plugins/context-pack"},
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": "Productivity",
        },
    ],
}
mp_file = agents_dir / "marketplace.json"
mp_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"[1] community marketplace manifest written: {mp_file}")

# ── 2. Add Divergent Thinking + Strict Execution rules to global AGENTS.md ──
agents_md = CODEX / "AGENTS.md"
current = agents_md.read_text(encoding="utf-8")

NEW_SECTIONS = (
    "\n\n"
    "## Divergent Thinking Defaults\n"
    "- For non-trivial tasks, explicitly enumerate **at least 2-3 alternative approaches** before picking one, and briefly state tradeoffs.\n"
    "- Question the framing of every request: is the stated problem the real problem? Surface the underlying need when it differs from the surface request.\n"
    "- For analysis or estimation tasks, approach from at least two angles (data-driven, logical deduction, edge-case stress-test, user-impact perspective) before drawing a conclusion.\n"
    "- When implementing something, also ask: what could go wrong? what is missing? what would make this more robust?\n"
    "- Prefer depth-first exploration on ambiguous problems before narrowing to a single solution path.\n"
    "- If the first approach is blocked, explicitly name 1-2 alternative strategies rather than stopping or retrying the same path.\n"
    "\n"
    "## Strict Execution Defaults\n"
    "- **Never declare a task complete** without verifiable evidence: the file exists and has expected size/content, the command exited 0, the key output line is present.\n"
    "- After writing a file, confirm its byte size and first + last meaningful lines.\n"
    "- After running a command, confirm the exit code and quote the key result line.\n"
    "- Do not skip verification steps even when the action 'should have' worked.\n"
    "- For multi-step tasks, maintain an explicit numbered checklist; mark a step complete **only after verifying** it, not when it was merely attempted.\n"
    "- If verification fails, stop and diagnose before retrying. Do not retry the same failing approach more than twice without changing strategy.\n"
    "- Before declaring a bug fixed, reproduce the original failure path and confirm it no longer triggers.\n"
)

if "## Divergent Thinking Defaults" not in current:
    agents_md.write_text(current + NEW_SECTIONS, encoding="utf-8")
    print("[2] Added Divergent Thinking + Strict Execution sections to AGENTS.md")
else:
    print("[2] Sections already present, skipped")

# ── 3. Change personality in config.toml ─────────────────────────────────────
config_file = CODEX / "config.toml"
config = config_file.read_text(encoding="utf-8")
if 'personality = "pragmatic"' in config:
    config = config.replace('personality = "pragmatic"', 'personality = "thorough"')
    config_file.write_text(config, encoding="utf-8")
    print("[3] Changed personality: pragmatic -> thorough")
elif 'personality = "thorough"' in config:
    print("[3] personality already set to thorough")
else:
    personality_lines = [l for l in config.splitlines() if "personality" in l]
    print(f"[3] personality line not found as expected; existing: {personality_lines}")

# ── 4. Update CODEX_LEARNING_MEMORY.md ───────────────────────────────────────
mem_file = CODEX / "CODEX_LEARNING_MEMORY.md"
mem = mem_file.read_text(encoding="utf-8")
note = (
    "\n\n"
    "## Behavioral Quality Improvements (2026-05-25)\n\n"
    "- community marketplace manifest was missing; created `.agents/plugins/marketplace.json` to fix startup error. Affected plugins: chrome-devtools, context-pack.\n"
    "- Added 'Divergent Thinking Defaults' and 'Strict Execution Defaults' sections to global AGENTS.md.\n"
    "  - Divergent: always enumerate 2-3 alternatives before choosing; question problem framing; multi-angle analysis.\n"
    "  - Strict: verify file/command result before marking complete; maintain numbered checklist; don't retry same failing approach >2 times.\n"
    "- Changed config.toml personality from 'pragmatic' to 'thorough' to reduce tunnel-vision on the first solution path.\n"
    "- xcodebuildmcp MCP originates from build-ios-apps@openai-curated plugin (irrelevant on Windows Python work but benign).\n"
)
if "Behavioral Quality Improvements" not in mem:
    mem_file.write_text(mem + note, encoding="utf-8")
    print("[4] Updated CODEX_LEARNING_MEMORY.md")
else:
    print("[4] Already updated, skipped")

print("\nDone. All 4 fixes applied.")
