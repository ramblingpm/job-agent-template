# SETUP.md: instructions for the AI assistant doing the setup

> **Human?** You don't need to read this. Give your AI assistant this sentence:
> *"Set up my job agent by following SETUP.md in https://github.com/ramblingpm/job-agent-template"*

---

**AI assistant: this file is written for you.** The user wants their own private copy of this job agent,
running every day. Follow the phases in order and be friendly. Assume the user isn't technical: do everything
you can yourself, and when the user must act, give them one small, exact step at a time.

**The end state you're aiming for:**
1. A **private** GitHub repository owned by the user, created from the `ramblingpm/job-agent-template` template.
2. `profile.md` and `config.yaml` in it describe what this user is looking for.
3. The daily **Fetch jobs** workflow has run once successfully, and a "Jobs YYYY-MM-DD" issue exists.
4. Daily AI scoring is connected to the user's subscription, or the user knows how to ask for scores on demand.

**Ground rules**
- The repository must be **private**, because `profile.md` contains personal and CV information.
  Never make it public.
- Never ask the user for passwords, tokens or API keys in chat. Logins happen in their browser.
- This agent needs no API keys and no paid services beyond the user's Claude or ChatGPT subscription.
  Don't add any.
- Ask before creating anything outside this list: one GitHub repository and, optionally, one scheduled routine.

---

## Phase 0: Work out where you're running

Pick the **first** path that matches what you can actually do:

| You can… | Path |
|---|---|
| Run shell commands on the user's computer (Claude Code CLI or desktop, Codex CLI) | **Path A: you do almost everything** |
| Only chat (claude.ai, ChatGPT), or you're in a cloud sandbox without the user's GitHub login | **Path B: you guide, the user clicks** |

To check, try running `git --version`. If you can't run commands, use Path B.

---

## Path A: you have a terminal

### A1. GitHub CLI and login
1. Check `gh --version`. If it's missing, install it:
   - macOS: `brew install gh` (if there's no Homebrew, switch to Path B)
   - Windows: `winget install --id GitHub.cli`
   - Linux: follow https://github.com/cli/cli#installation
2. Check `gh auth status`.
   - If they're **not logged in**, the user must log in interactively. Ask them to run this themselves
     (in Claude Code they can type it with a leading `!`):
     `gh auth login -h github.com -p https -w -s workflow`
     Then they approve it in the browser.
   - If they **are logged in** but the token scopes don't include `workflow`, ask them to run
     `gh auth refresh -h github.com -s workflow`. Without this scope, pushing the workflow files fails with
     *"refusing to allow an OAuth App to create or update workflow"*.
3. Run `gh api user --jq .login` to get their GitHub username. You'll need it as `<user>` below.

### A2. Create the private copy
Ask: *"What should I call your repository? I'd suggest `my-job-agent`."* Then:

```bash
gh repo create <name> --template ramblingpm/job-agent-template --private --clone
cd <name>
```

- If the clone comes up empty or fails, GitHub may still be copying the template. Wait 5 seconds and run
  `gh repo clone <user>/<name>`.
- If you get *"Could not resolve to a Repository"*, the template isn't reachable from this account yet. Stop
  and tell the user.

Confirm it's private: `gh repo view --json visibility --jq .visibility` should print `PRIVATE`.

### A3. Profile interview
Read `AGENTS.md` (Task 2) and `profile.md`. Then interview the user conversationally, a few questions at a time:
- Which roles or titles are they after? Ask for Swedish and English variants, such as "produktchef" and "product manager".
- What seniority? Where are they willing to work, and how do they feel about remote, hybrid and on-site?
- Must-haves, nice-to-haves and deal-breakers.
- A short background. Offer: *"You can paste your CV or LinkedIn summary, or point me to the file, and I'll
  summarize it."*

Rewrite `profile.md` in the user's language, keeping its headings. Update `config.yaml`:
`search.queries` (3–6 queries), `location.places`, `filters.title_must_contain_any`, `filters.title_exclude`
and `filters.boost_keywords`. Keep the comments.

### A4. Tune the search with a dry run
```bash
python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt
.venv/bin/python -m jobagent preview 14
```
This writes nothing. Show the user the result in plain words, for example: *"In the last two weeks this would
have found 23 jobs (about 2 a day). Here are the titles…"* and the dropped titles. Adjust `config.yaml` and
preview again until they're happy. Good targets are:
- **Too few** (under 1 a week): broaden the queries, empty `places`, or relax `title_must_contain_any`.
- **Too many irrelevant ones**: add words to `title_exclude`. The AI also filters later, so a little noise is fine.

On Windows, use `.venv\Scripts\python` instead of `.venv/bin/python`.

### A5. Save and start it
```bash
git add profile.md config.yaml
git commit -m "Set up my profile"
git push
gh workflow run "Fetch jobs"
```
Wait about 10 seconds, then watch it:
`gh run watch $(gh run list --workflow fetch.yml --limit 1 --json databaseId --jq '.[0].databaseId') --exit-status`

Then check the result with `gh api "repos/<user>/<name>/issues?labels=jobs" --jq '.[].html_url'`.
If it's empty, wait 15 seconds and try once more: new issues sometimes take a moment to appear.
- **There's an issue**: it's working. Then `git pull` to get the fetched inbox.
- **The run succeeded but there's no issue**: no new jobs matched today. That's fine, and it will run again
  tomorrow at 07:00.
- **The run failed** on a push or permission error: run
  `gh api -X PUT repos/<user>/<name>/actions/permissions/workflow -f default_workflow_permissions=write`,
  then re-run the workflow. For anything else, read the log with `gh run view --log-failed` and fix the problem.

### A6. First scoring (shows the user the payoff)
Run `git pull`, then do **Task 1 in `AGENTS.md`** yourself and push the result. About a minute later the issue
updates with AI scores and gets a "Scores are in" comment. Show the user the issue link from A5.

### A7. Daily scoring: go to Phase C.

---

## Path B: you can only chat, so guide the user

Give the user **one step at a time** and wait until they say it's done. Use exact button names.

1. **Copy the template.** Open https://github.com/ramblingpm/job-agent-template, then click
   **Use this template → Create a new repository**. Name it `my-job-agent`, choose **Private**, and click
   **Create repository**. If they don't have a GitHub account, have them create a free one at
   https://github.com/signup first.
2. **Profile interview.** Interview them as described in A3. Then produce the **complete** new contents of
   `profile.md`, and separately of `config.yaml`, each in a single code block.
3. **Paste them in.** In their repository, click `profile.md` → ✏️ (Edit) → select all → paste →
   **Commit changes…** → **Commit changes**. Then do the same for `config.yaml`.
4. **First run.** Have them open the **Actions** tab, then **Fetch jobs** → **Run workflow** → **Run workflow**.
   After about a minute there's a green tick, and the **Issues** tab has "Jobs YYYY-MM-DD". (If no jobs matched
   today, there's no issue; that's fine.)
   If it fails with a permission error, have them go to **Settings → Actions → General → Workflow permissions**,
   choose **Read and write permissions**, click **Save**, and run it again.
5. Continue with **Phase C**.

You can't tune the search with a dry run here. If there are too few or too many results after a few days,
update `config.yaml` with them.

---

## Phase C: daily AI scoring

Ask which subscription they have, then set up **one** of these.

### Claude Pro/Max: a scheduled routine (recommended; nothing to install)
Routines run in Anthropic's cloud on the user's subscription.
- **If you have a tool or command for creating Claude Code routines or scheduled cloud tasks** (for example
  `/schedule`), create one with:
  - **Repository:** `<user>/<name>`
  - **Schedule:** daily at 08:00 Europe/Stockholm, which is after the 07:00 fetch
  - **Prompt:** `Score today's jobs following AGENTS.md`
  - **Branch pushes:** the default `claude/` prefix is fine.
- **Otherwise**, guide the user:
  1. Open https://claude.ai/code and sign in.
  2. If asked, connect GitHub and give the Claude GitHub app access to `<name>`.
  3. Go to **Routines → New routine** and use the repository, schedule and prompt above, then **Save**.
  4. Click **Run now** to test it. About 5 minutes later the issue should show AI scores.

### ChatGPT Plus/Pro: Codex, on demand
Codex can't currently run this on a schedule from a subscription, so scoring is on demand. Guide the user:
1. Open https://chatgpt.com/codex and connect GitHub (give it access to `<name>`).
2. Create an environment for `<name>`. Under **Setup script**, enter `pip install -r requirements.txt`.
3. Whenever they want scores (once a day works well, and the ChatGPT phone app is fine for this), tell
   Codex: **"Score today's jobs"**. When it offers to, let it push the branch or create the PR. They don't need
   to merge it.

### Optional: a terminal user with Claude who wants scoring inside the morning GitHub run
Ask the user to run `claude setup-token` themselves (or `npx @anthropic-ai/claude-code setup-token`), then
`gh secret set CLAUDE_CODE_OAUTH_TOKEN`, pasting the token **into the terminal, not into chat**. The Fetch jobs
workflow picks it up automatically.

---

## Phase D: wrap up
Tell the user, briefly:
- Their repository link, and that it's private.
- New jobs arrive every morning as a GitHub issue. GitHub emails them; if not, they should check
  https://github.com/settings/notifications.
- To change what they're looking for, they can just ask you (or any Claude or ChatGPT session with access to the
  repository) to *"update my job profile"*.
- How AI scoring runs for them: the daily routine, or asking Codex "Score today's jobs".
