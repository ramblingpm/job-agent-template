# Job agent 🇸🇪

**A personal AI job scout for the Swedish job market.** Every morning it pulls new ads from Platsbanken
(Arbetsförmedlingen), and your own Claude or ChatGPT reads each one against *your* profile. You get the results
as a GitHub issue in your inbox.

> 🇸🇪 *En personlig jobbagent: hämtar nya annonser från Platsbanken varje morgon och låter din egen Claude eller
> ChatGPT bedöma dem mot din profil. Du behöver bara ett GitHub-konto och ett Claude- eller ChatGPT-abonnemang.*

**What you need:** a free GitHub account, plus a Claude Pro/Max or ChatGPT Plus/Pro subscription.
There are no API keys, nothing to pay per run, and nothing to install.

```
 every morning (free)             your AI (your subscription)          you
 ┌──────────────────────┐        ┌───────────────────────────┐        ┌─────────────────┐
 │ GitHub Action fetches│  ───▶  │ Claude / Codex scores each│  ───▶  │ GitHub issue +  │
 │ new Platsbanken ads  │        │ ad against profile.md     │        │ email: top jobs │
 └──────────────────────┘        └───────────────────────────┘        └─────────────────┘
```

Even without the AI step, you still get a daily issue with the new ads, ranked by keyword match.

---

## ⚡ The easy way: two clicks, then just chat

**1. [Create my private copy →](https://github.com/new?owner=@me&template_owner=ramblingpm&template_name=job-agent-template&name=my-job-agent&visibility=private)**
Everything is filled in (name `my-job-agent`, **Private**), so just click **Create repository**.

**2. Open [claude.ai/code](https://claude.ai/code), pick `my-job-agent`, and say:**
```
Set me up
```
If `my-job-agent` isn't in the list, use the option there to give Claude access to more repositories.

Claude interviews you about the job you want (any occupation), sets up the search, shows you what it finds,
and scores your first batch of jobs. A few minutes later, your first ranked job list is in the **Issues** tab.

<sub>Using Claude Code or Codex on your own computer instead? Say *"Set up my job agent by following SETUP.md in
https://github.com/ramblingpm/job-agent-template"* and it does both steps for you. ChatGPT users: do step 1, then
open the repository in [Codex](https://chatgpt.com/codex) and say "Set me up".</sub>

---

## Setup by hand (about 10 minutes)

### 1. Make your own copy
Click **Use this template → Create a new repository** at the top of this page.
Choose **Private**, because your profile will describe you and your CV.

### 2. Tell it what you're looking for
In your new repository, edit these two files (click the file, then the ✏️ pencil icon):

- **`profile.md`** describes what you want: roles, seniority, location, must-haves, deal-breakers and a short CV.
  The AI scores every ad against this file.
- **`config.yaml`** sets what to fetch: search terms, cities, and title words to keep or drop.

Shortcut: once you've connected your AI in step 4, just ask it **"Help me set up my profile"**. It will interview
you and update both files.

### 3. First run starts by itself
Saving `profile.md` or `config.yaml` starts a search over the last two weeks. About two minutes later you'll see
an issue called **"Jobs YYYY-MM-DD"**, and `data/last-run.md` shows what was found. From now on it runs by
itself every morning at 07:00.

### 4. Connect your AI, picking one of the options below

<details open>
<summary><b>Option A: Claude Pro/Max, fully automatic (recommended)</b></summary>

1. Go to [claude.ai/code](https://claude.ai/code) and connect your GitHub account when asked. Give it access to
   your job-agent repository.
2. Open **Routines → New routine**:
   - **Repository:** your job-agent repository
   - **Schedule:** daily at 08:00, which is after the morning fetch
   - **Prompt:** `Score today's jobs following AGENTS.md`
3. Save. To test it now, click **Run now**.

Each morning Claude scores the new ads and pushes the result. The issue then updates itself and you get an email.
Routines use your normal Claude usage allowance.
</details>

<details>
<summary><b>Option B: ChatGPT Plus/Pro, with Codex</b></summary>

1. Go to [chatgpt.com/codex](https://chatgpt.com/codex) and connect GitHub. Give it access to your job-agent
   repository.
2. Create an environment for the repository. Under **Setup script**, enter `pip install -r requirements.txt`.
3. Whenever you want scores, which you can do every morning from the ChatGPT app, ask Codex in that environment:
   **"Score today's jobs"**. When Codex offers to, let it create the PR or push the branch.
   You don't need to merge it. The repository picks up the scores and updates the issue.
</details>

<details>
<summary><b>Option C: Claude, inside the GitHub Action (for people comfortable with a terminal)</b></summary>

This scores the jobs within the same morning run. On any computer with Node.js, run
`npx @anthropic-ai/claude-code setup-token` and log in with your Claude account. In your repository, go to
**Settings → Secrets and variables → Actions → New repository secret** and add `CLAUDE_CODE_OAUTH_TOKEN`
with the token. That's it: the **Fetch jobs** workflow uses it automatically.
</details>

<details>
<summary><b>On demand: either subscription, any time</b></summary>

Open the repository in Claude Code on the web or in Codex, and say **"Score today's jobs"**.
</details>

### 5. Make sure the emails reach you
GitHub emails you about new issues in your own repositories by default. If you don't get them, check
[github.com/settings/notifications](https://github.com/settings/notifications) and make sure **Email** is
ticked under *Participating* and *Watching*.

---

## Everyday use
- Read the daily **Jobs** issue. Close it when you're done, or keep it open as a shortlist.
- Change what you're looking for any time by editing `profile.md` and `config.yaml`, or by asking your AI.
- Seen ads are remembered (`data/seen.json`), so each ad shows up only once.

## FAQ
**Does this cost anything?** Not beyond your subscription. Private repositories get 2,000 free GitHub Actions
minutes a month, and this uses about one minute a day. The AI scoring counts towards your normal Claude or
ChatGPT usage.

**Which jobs does it see?** Everything published on [Platsbanken](https://arbetsformedlingen.se/platsbanken),
through Arbetsförmedlingen's free and open JobTech API. That includes many ads that are also on LinkedIn and
company career pages, but not all of them.

**Is my data private?** Your profile stays in your private repository. Your AI reads it only when it scores your
jobs.

**What about prompt injection in job ads?** The AI is told to treat ad text as untrusted data. Issue text is
cleaned so ads can't add links or @-mention people. See the *Security* section in `AGENTS.md`.

**The workflow failed with "permission denied" when pushing.** Go to **Settings → Actions → General →
Workflow permissions** and choose **Read and write permissions**.

## For tinkerers
```bash
pip install -r requirements.txt -r requirements-dev.txt
python -m jobagent fetch            # fetch into data/inbox/<today>.json
python -m jobagent pending          # dates waiting for AI scores
python -m jobagent validate <date>  # check data/scored/<date>.json
python -m jobagent render <date>    # print the issue body
python -m pytest
```
`AGENTS.md` contains the full instructions the AI follows, including the scoring rubric and output format.

MIT licensed. Job data comes from [JobTech Dev](https://jobtechdev.se) / Arbetsförmedlingen.
