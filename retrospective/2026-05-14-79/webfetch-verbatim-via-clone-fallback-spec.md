# Spec: `webfetch-verbatim-via-clone-fallback`

## Intent

WebFetch routes the fetched page through a small AI processing model. That model **summarizes content even when the prompt explicitly asks for verbatim output**. In this session, fetching `parallel-subagent-fanout/SKILL.md` from raw.githubusercontent.com returned the full file, but `subagent-prompting/SKILL.md` and `self-retrospective/SKILL.md` came back as 200-300-word summaries despite the prompt: "This is a raw markdown file. Output its content verbatim, character-for-character, with no summarization."

The cost of accepting a summary as input: design work proceeds from a 70% lossy compression of the source, missing exact wording, missing the trap-list at the bottom, missing the YAML frontmatter, missing per-section step counts. The cost of catching it on the second attempt and switching transport: one extra Bash command (`git clone --depth 1`).

When verbatim content is needed (skill content, spec text, code, anything where re-summarization corrupts the artifact), use git clone or a direct REST download with `curl` instead of WebFetch.

## Trigger

Activate when the agent needs the **exact bytes** of one or more files from a public Git host (GitHub, GitLab, etc.) and one of these applies:

- The content will be copied verbatim into the working repo.
- The content is a skill / spec / contract that requires precise wording.
- The content includes code, frontmatter, or tables where format integrity matters.

**Direct triggers**:
- "Copy these files verbatim from <repo>"
- "Read this skill / spec / file into context"
- "Install this skill from <repo>"

**Proactive triggers**:
- User has explicitly warned about summarization in this session.
- A prior WebFetch attempt returned a summary instead of the requested content.
- The file is >2 KB and contains structured content (tables, code blocks, frontmatter).

**Negative triggers** (use WebFetch instead):
- The user only needs a summary or extraction (e.g. "what does this PR change?").
- The content is rendered HTML where the agent wants a readable digest.
- The file is small (<500 bytes) and clearly text.

## Inputs

- A list of file paths (or directory paths) on the source host.
- The source repo URL.
- An optional branch / tag / ref (defaults to default branch).
- A destination path in the working repo.

## Outputs

- The files at their destination paths, byte-identical to source.
- An optional manifest (one line per file: `<sha256> <path>`).

## Workflow

1. **Determine scope.** Is it (a) one or two specific files, or (b) one or more directories?
2. **If one or two files**, use `curl` against `https://raw.githubusercontent.com/<owner>/<repo>/<ref>/<path>` and pipe to the destination. Verify size > 0 after download.
3. **If one or more directories** or unknown file inventory, clone the source repo into a temp directory:
   ```bash
   mkdir -p /tmp/<repo>-clone
   cd /tmp/<repo>-clone
   git clone --depth 1 https://github.com/<owner>/<repo>.git .
   ```
4. **Copy with `cp -r`** to preserve file modes (executable bits matter for shell scripts).
5. **Verify byte-equivalence** for at least one file: `sha256sum` source and destination, compare. If they differ, abort and inspect.
6. **Clean up the temp directory** when done: `rm -rf /tmp/<repo>-clone`.

## Concrete examples

### Example 1: install 5 skills from a sibling repo

User: "Copy these 5 skills from `lago-morph/software-factory` into `.claude/skills/`. Do not use WebFetch."

Agent:
```bash
mkdir -p /tmp/software-factory-clone
cd /tmp/software-factory-clone
git clone --depth 1 https://github.com/lago-morph/software-factory.git .
cd /home/user/poc-github-ai-sandbox
for skill in parallel-subagent-fanout post-edit-reread-pass retro-coverage-audit-and-backfill self-retrospective subagent-prompting; do
  rm -rf .claude/skills/$skill
  cp -r /tmp/software-factory-clone/.claude/skills/$skill .claude/skills/
done
rm -rf /tmp/software-factory-clone
```

Result: 15 files including an executable shell script, all byte-identical to source. Confirmed via `git diff` showing 0 unexpected changes against a follow-up clone.

### Example 2: WebFetch tried first, fell back to clone

Agent attempts:
```
WebFetch(url=https://raw.githubusercontent.com/lago-morph/software-factory/main/.claude/skills/self-retrospective/SKILL.md,
         prompt="Output the file verbatim, character-for-character, no summarization.")
```

Response: a ~300-word summary mentioning "main report" and "UTC date verification" — not the full 530-line skill. Retry with even more explicit prompt: same summary.

Agent switches:
```bash
git clone --depth 1 https://github.com/lago-morph/software-factory.git /tmp/sf
cat /tmp/sf/.claude/skills/self-retrospective/SKILL.md
```

Result: full 530-line verbatim content. Cost: 2 seconds, one Bash call.

## Anti-patterns

- **Re-prompting WebFetch with stronger language.** "Output verbatim" doesn't disable the processing model's summarization tendency. After one summary response, switch transport — don't retry the same call hoping for a different result.
- **Trusting WebFetch summaries for content that will be copied verbatim.** If the agent is going to write the file to disk, the agent needs every byte. A summary is unfit for that purpose.
- **Cloning the whole repo when one file is needed.** Use `curl https://raw.githubusercontent.com/...` for a single file — faster, less cleanup.
- **Forgetting `--depth 1`.** Shallow clone is enough for verbatim copying. Skipping the depth flag downloads full history for no benefit.
- **Skipping the cleanup `rm -rf`.** Temp directories accumulate; leave the sandbox cleaner than you found it.
- **Skipping mode-preservation verification.** `cp -r` preserves the executable bit, but if you `cat src > dst` you lose it. If the file is a script, verify with `ls -l`.

## Acceptance criteria

1. For at least one bundled file, `sha256sum source dest` produces matching hashes.
2. Executable bits on shell scripts are preserved (`ls -l` shows `x` in the mode).
3. The temp directory is removed after the copy completes.
4. The agent does NOT retry WebFetch with stronger language after observing a summary response.
5. Skill activates on user phrases "verbatim", "byte-for-byte", or "do not use WebFetch".

## Files this skill creates / modifies

- Files at the user-specified destination paths (e.g. `.claude/skills/<name>/`).
- Optionally `manifest.txt` at the destination root with sha256 sums.
- Does NOT modify any source content.
- Does NOT leave artifacts under `/tmp/` after exit.
