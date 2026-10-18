# SETUP.md: instructions for the AI assistant doing the setup

> **Human?** You don't need to read this. See "The easy way" in the README: create your copy with one click, then
> tell Claude **"Set me up"**.

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

Pick the **first** row that matches:

| Situation | Path |
|---|---|
| You're in a **cloud sandbox**: Claude Code on the web, a Claude routine, or Codex cloud. Typical signs: the `CLAUDE_CODE_REMOTE` environment variable is set, or you were started inside a cloned GitHub repository and `gh` isn't logged in. | **Path S: the sandbox works through git** |
| You can run commands on the **user's own computer** (Claude Code CLI or desktop, Codex CLI) | **Path A: you do almost everything** |
| You can only chat (claude.ai, ChatGPT), with no command execution | **Path B: you guide, the user clicks** |

To check whether you can run commands, try `git --version`.

---

## Path S: cloud sandbox (Claude Code on the web, routines, Codex cloud)

Sandboxes can only reach the repository they were started on, usually only push to their own branch, and often
can't reach the job API. **Don't try to log in to GitHub or create repositories from here.** That gets blocked
(for example with HTTP 415). Instead, the repository's GitHub Actions do that work. `sync.yml` copies what you
push on any branch to `main`, runs a fetch, and writes the result to `data/last-run.md`, which you read back
with `git fetch`.

### S1. Which repository are you in?
Run `git remote get-url origin`.
- **It's `ramblingpm/job-agent-template` (the template itself)**: you can't set up from here. Tell the user,
  in these two steps:
  1. *"Click this link to create your private copy, then click **Create repository**:"*
     https://github.com/new?owner=@me&template_owner=ramblingpm&template_name=job-agent-template&name=my-job-agent&visibility=private
  2. *"Then start a new Claude Code session on **my-job-agent** (at claude.ai/code, pick it in the repository
     list; if it isn't listed, use the option to give Claude access to more repositories), and say **Set me up**."*

  Then stop. Don't run the interview here, because the answers would be lost.
- **It's the user's own copy:** continue with S2.

### S2. Interview and save
1. Run **[The interview](#the-interview)** below, steps 1–5. Skip the `suggest` and `preview` commands if they fail
   with network errors; they'll be replaced by the report in S3.
2. Commit `profile.md` and `config.yaml`, then push to your current branch (`git push -u origin HEAD`).
   Remember the output of `python -m jobagent fingerprint`; if Python or the packages aren't available, use
   `sha256sum config.yaml | cut -c1-12`.
3. Tell the user: *"Saved. GitHub is now running your first search over the last two weeks. That takes about
   two minutes."*

### S3. Read the report and tune it
Wait for the report: repeat `git fetch -q origin main && git show origin/main:data/last-run.md | head -3` every
20 seconds, for up to 6 minutes, until the `Config:` line equals your fingerprint.
- **The report starts with `ERROR`**: your `config.yaml` was rejected (main kept the previous one). Fix it and
  push again.
- **Otherwise**, summarize it for the user in plain words, for example *"Over the last two weeks this found 14
  jobs, about 1 a day: [3–5 example titles]. It skipped things like [2–3 dropped titles]."* Ask whether that
  looks right, with the options **Looks good** and **Adjust the search**. To adjust, edit `config.yaml` (see
  the interview's step 5), push, and wait for the new fingerprint again.
  Tuning doesn't fetch the same ads again: each run only counts ads it hasn't seen before.
- **No matching report after 6 minutes**: tell the user to open the **Actions** tab of their repository and check
  whether **Sync from AI** shows a red ✗. The usual fix: **Settings → Actions → General → Workflow permissions →
  Read and write permissions → Save**, then ask you to push again.

### S4. First scores
1. Get the new ads: `git fetch -q origin main && git checkout origin/main -- data/inbox data/scored`.
2. Do **Task 1 in `AGENTS.md`**, scoring every pending date, and push the scores to your branch. `sync.yml`
   publishes them, so there's nothing to merge.
3. Tell the user: *"Done! Open the **Issues** tab of my-job-agent: your first job list is there, ranked against
   your profile. GitHub also emails you about new ones."*

### S5. Daily scoring
Continue with **Phase C** below. Claude can't create a routine from inside a sandbox, so give the user the click
steps.

---

## Path A: you can run commands

### A1. GitHub CLI and login
1. Check `gh --version`. If it's missing, install it:
   - macOS: `brew install gh`
   - Windows: `winget install --id GitHub.cli`
   - Linux or sandbox: `(type -p apt-get && sudo apt-get install -y gh) || conda install -y gh`, or follow
     https://github.com/cli/cli#installation
   - If installing fails, switch to Path B.
2. **Ignore pre-set tokens.** Some environments set `GH_TOKEN` or `GITHUB_TOKEN` to a token that only works for
   the sandbox's own repository; `gh auth status` then reports *"Failed to log in … using token (GH_TOKEN)"* or an
   invalid token. `gh` always prefers those variables over a real login, so **put `env -u GH_TOKEN -u GITHUB_TOKEN`
   in front of every `gh` command in this guide**. Shell state may not carry over between your commands, so
   repeat it every time. Below, `gh` stands for that whole prefix.
3. Run `gh auth status`.
   - **Logged in, with `workflow` in the token scopes**: go to step 4.
   - **Not logged in**: start the browser login yourself **in the background**, with a 15-minute timeout and its
     output sent to a file:
     `env -u GH_TOKEN -u GITHUB_TOKEN gh auth login -h github.com -p https -w -s workflow </dev/null >gh-login.txt 2>&1`
     After a few seconds, read `gh-login.txt`. It contains a one-time code like `ABCD-1234`. Tell the user:
     *"Open https://github.com/login/device, enter code **ABCD-1234** and click Authorize. Tell me when it says
     you're done."* Then wait until the background command exits and run `gh auth status` again.
     If the user is at their own terminal, they can run the same command themselves instead
     (in Claude Code, by typing it with a leading `!`).
   - **Logged in, but `workflow` is missing from the scopes**: do the same with
     `gh auth refresh -h github.com -s workflow`. Without this scope, pushing the workflow files fails with
     *"refusing to allow an OAuth App to create or update workflow"*.
   - If no code appears, or the login fails (for example, a network block), switch to **Path B**. Tell the user
     why in one sentence.
4. Run `gh auth setup-git`, so that `git push` to the user's new repository uses this login.
5. Run `gh api user --jq .login` to get their GitHub username. You'll need it as `<user>` below.

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
- **Sandbox only:** if you were started inside some other repository, create and clone the new one *next to it*,
  not inside it.

Confirm it's private: `gh repo view --json visibility --jq .visibility` should print `PRIVATE`.

### A3. Profile interview
Follow **[The interview](#the-interview)** below, including step 5 (writing the files). Keep the comments in
`config.yaml`.

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
```
Pushing these files starts the **Sync from AI** workflow automatically. It runs a first fetch over the last 14
days, which takes about two minutes. Wait about 10 seconds, then watch it:
`gh run watch $(gh run list --workflow sync.yml --limit 1 --json databaseId --jq '.[0].databaseId') --exit-status`

Then run `git pull` and read `data/last-run.md`. It contains how many ads were found and kept, and the titles.
Summarize it for the user, and check `gh api "repos/<user>/<name>/issues?labels=jobs" --jq '.[].html_url'` for
the issue (if it's empty, try again after 15 seconds).
- **Kept 0 jobs**: broaden the search (A4) and push again.
- **The run failed** on a push or permission error: run
  `gh api -X PUT repos/<user>/<name>/actions/permissions/workflow -f default_workflow_permissions=write`,
  then push again. For anything else, read the log with `gh run view --log-failed` and fix the problem.

### A6. First scoring (shows the user the payoff)
Do **Task 1 in `AGENTS.md`** yourself and push the result. About a minute later the issue updates with AI scores
and gets a "Scores are in" comment. Show the user the issue link from A5.

### A7. Daily scoring: go to Phase C.

---

## Path B: you can only chat, so guide the user

Give the user **one step at a time** and wait until they say it's done. Use exact button names.

1. **Copy the template.** Open https://github.com/ramblingpm/job-agent-template, then click
   **Use this template → Create a new repository**. Name it `my-job-agent`, choose **Private**, and click
   **Create repository**. If they don't have a GitHub account, have them create a free one at
   https://github.com/signup first.
2. **Profile interview.** Follow **[The interview](#the-interview)** below. Then produce the **complete** new contents of
   `profile.md`, and separately of `config.yaml`, each in a single code block.
3. **Paste them in.** In their repository, click `profile.md` → ✏️ (Edit) → select all → paste →
   **Commit changes…** → **Commit changes**. Then do the same for `config.yaml`.
4. **First run.** Saving the files starts the first search automatically, looking back two weeks. After about
   two minutes the **Issues** tab has "Jobs YYYY-MM-DD". If they open `data/last-run.md`, they can see what was
   found and kept. (If nothing matched, there's no issue; then broaden `config.yaml` together.)
   If the **Actions** tab shows a red ✗ with a permission error, have them go to **Settings → Actions → General →
   Workflow permissions**, choose **Read and write permissions**, click **Save**, and save a file again.
5. Continue with **Phase C**.

You can't tune the search with a dry run here. If there are too few or too many results after a few days,
update `config.yaml` with them.

---

## The interview

**Goal:** work out what kind of job this person is after (it can be anything: nurse, electrician, teacher,
developer, accountant…), understand what makes a job a good or bad match **for them**, and turn that into
`profile.md` and `config.yaml`. Don't assume any field.

**How to ask**
- **One question per message.** Never send a list of questions. Wait for each answer before asking the next.
- If you have a tool that shows clickable choices (for example `AskUserQuestion` in Claude Code, or the option
  buttons in the Claude and ChatGPT apps), **offer 3–6 options you generate for this person**, plus free text.
  Without such a tool, write the options as a short numbered list, so the user can just reply "2".
- Keep each message to one or two lines, plus the options. Skip anything you can already infer, and never ask
  for something the CV already says.

### Step 1: Open question
Ask: *"What kind of job are you looking for? Describe it in your own words, or paste your CV or LinkedIn
profile and I'll work it out."* No options here; this is free text.

### Step 2: Form a hypothesis and confirm it
From the answer, work out the occupation (or two or three closely related ones), the likely seniority and the
field or industry. Then confirm in one question with clickable options, for example:
*"Sounds like you're an experienced **[occupation]**. Which of these titles would you apply for?"*, offering
4–6 concrete titles in **Swedish and English**, as they appear in Swedish ads. Use multi-select if possible.
If you're unsure between two readings, make each one an option.

**If you can run commands**, check your title words against real ads before offering them:
`python -m jobagent suggest <word-stem>` (for example `suggest sjuksköt`, `suggest testa`, `suggest redovis`)
lists the occupation terms Swedish ads actually use, with counts. Prefer terms with high counts.

### Step 3: Fill the gaps, adapted to the field
Ask only what's still unknown, one question each, and generate options that fit **this** occupation:
1. **Level:** for example *Junior · Experienced · Senior · Lead · Manager*. Use the field's own terms; for a
   nurse that might be *Grundutbildad · Specialistsjuksköterska · Chef*.
2. **Where:** cities or regions that make sense given their answers, plus *Remote anywhere in Sweden* and
   *All of Sweden*.
3. **Work arrangement:** whatever matters in this field: remote/hybrid/on-site for office jobs; day/evening/
   night shifts for care, retail and industry; travel or field work; full-time or part-time.
4. **What makes a job a great match:** 2–3 *field-specific* signals. Ask yourself *"what would make this
   person say yes to one ad and no to another?"* For example: tech stack for developers, ward or specialty for
   nurses, residential vs. industrial work for electricians, grade levels and subjects for teachers, or
   industry and company size for many office roles.
5. **Requirements they meet or need:** licences and certificates common in the field (legitimation,
   behörighet, driving licence B/C, security clearance), plus languages.
6. **Deal-breakers:** options typical for the field (for example *Staffing/consulting agencies · Temporary
   contracts · Night shifts · Long commute · Specific employers or industries*), plus *None*.

Usually 5–8 questions in total are enough. Stop asking once you could explain to a friend which ads this person
would and wouldn't want.

### Step 4: Confirm
Show a summary of at most five lines (titles, level, where, the top match signals, deal-breakers) and ask
*"Look right?"* with the options **Yes, save it** and **Change something**.

### Step 5: Write the files
- **`profile.md`:** fill in every section, in the user's language. Put the field-specific signals from
  step 3.4 under *"What makes a great match"*; that section is what the scoring AI uses most.
- **`config.yaml`:** this is only the coarse net. The AI scoring does the fine matching, so the net should be a
  bit too wide rather than too narrow.
  - `search.queries`: 3–8 searches covering Swedish and English titles, plural forms, and common synonyms
    (for example `"sjuksköterska", "specialistsjuksköterska", "nurse"`).
  - `filters.title_must_contain_any`: short word stems that any relevant title contains (for example `"sjuksköt"`,
    `"nurse"`). If titles in this field vary too much to name, leave it empty.
  - `filters.title_exclude`: obvious neighbouring roles that share a word but aren't wanted (for example
    `"test"` for a developer who doesn't want QA work, or `"chef"` for someone who doesn't want to manage).
  - `filters.boost_keywords`: the field-specific match signals (for example `"python"`, `"akutsjukvård"`,
    `"senior"`).
  - `location.places`: from step 3.2. Leave it empty for all of Sweden.
- **If you can run commands, test it** with `python -m jobagent preview 14` (see A4). Aim for roughly 1–5 kept
  ads a day. Look at the kept and dropped titles, and adjust until the kept ones look right and nothing obviously
  relevant was dropped.

## Phase C: daily AI scoring

Don't ask which subscription they have if you can tell: if you are Claude, use the Claude option, and if you are
ChatGPT or Codex, use the ChatGPT option. Then set up **one** of these.

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
