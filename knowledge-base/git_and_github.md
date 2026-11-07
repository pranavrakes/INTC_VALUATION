# Git and GitHub — the basics

A beginner's guide to how we share code on this project: what Git and GitHub are,
the everyday workflow, and how to do it all from PyCharm and the GitHub website.

---

## 1. Git vs GitHub — what's the difference?

- **Git** is a program on your computer that records the history of your project. Every
  time you save a "snapshot" (a **commit**), Git remembers exactly what every file looked
  like. You can see who changed what and when, and go back to any earlier version.
- **GitHub** is a website (github.com) that stores a copy of the project online, so two
  or more people can share it. It adds collaboration features on top of Git: reviewing
  each other's changes, commenting, and showing documents nicely formatted.

Analogy: Git is like "Track Changes + Save As versions" for a whole folder.
GitHub is like Google Drive for that folder, plus a place to discuss changes.

## 2. Repositories — local and remote

A **repository** ("repo") is a project folder that Git is tracking.

| | Local repository | Remote repository |
|---|---|---|
| **Where** | On your own computer, e.g. `~/dev/python/intc_valuation` | On GitHub: `github.com/pranavrakes/INTC_VALUATION` |
| **Who sees it** | Only you | Everyone with access |
| **Why** | You work here: edit, run, commit — even offline | The shared "official" copy that we both sync with |
| **Name in Git** | — | Usually called **`origin`** |

Each of us has our own local copy. We never edit each other's computers — we exchange
changes through the remote on GitHub.

```
  Your computer                GitHub                  Other persons's computer
 ┌─────────────┐   push →   ┌──────────┐   ← push   ┌─────────────┐
 │ local repo  │            │  remote  │            │ local repo  │
 │             │   ← pull   │ (origin) │   pull →   │             │
 └─────────────┘            └──────────┘            └─────────────┘
```

**Where does Git keep its history?** In a hidden folder called **`.git`** inside the
project folder. Don't edit or delete it — deleting it erases all history from that copy.

**Clone** = download a remote repo to your computer for the first time (creates the
local repo, with full history). You only do this once per computer.

## 3. The stages of a change

A change goes through four stages before the other person can see it:

```
 1. Modified       2. Staged          3. Committed        4. Pushed
 (unstaged)
 You edited    →   You picked it   →  Saved as a      →   Uploaded to
 a file            for the next       snapshot in         GitHub
                   snapshot           your LOCAL repo
```

| Stage | What it means | Command |
|---|---|---|
| **Untracked** | A brand-new file Git has never seen. | — |
| **Modified / unstaged** | You changed a file, but haven't told Git to include it yet. | — |
| **Staged** | You've marked the change to go into the next commit. Lets you commit some files and not others. | `git add <file>` |
| **Committed** | A permanent snapshot in your **local** history, with a message describing it. Not on GitHub yet! | `git commit -m "message"` |
| **Pushed** | Your commits are uploaded to GitHub. Now the other person can get them. | `git push` |

> **Common mistake:** committing and forgetting to push. Your work is safe on your
> computer, but nobody else can see it until you push.

**Good commit messages** say *what* and *why* in a short sentence:
✅ `Add WACC calculation with 4 beta windows`  ❌ `stuff`, `fix`, `changes`

### What Git ignores

The **`.gitignore`** file lists things Git should never track: the `.venv/` folder,
downloaded data (`data/raw/`), PyCharm's `.idea/` settings, `__pycache__/`. These are
either big, personal, or can be regenerated. Never commit passwords or keys.

## 4. Getting the other person's changes: fetch and pull

| Action | What it does | Analogy |
|---|---|---|
| **Fetch** | Downloads news from GitHub (new commits, new branches) but **doesn't change your files**. Safe any time. | Checking your mailbox but not opening the letters. |
| **Pull** | Fetch **and** apply the new commits to your current branch, so your files update. | Fetching the mail and filing it. |

**Habit:** pull before you start working, so you're building on the latest version.

## 5. Branches

A **branch** is a separate line of work. It lets you try something without
disturbing the main version.

- **`master`** (on some projects called `main`) is the main branch — the "good" version.
- For any new piece of work, create a branch from master, e.g. `knowledge-base-plus-plan`.
- Commit to your branch as much as you like; master is unaffected.
- When the work is ready, it's **merged** back into master.

```
master:   A ── B ──────────────── E   (merge)
                \                /
my-branch:       C ──── D ──────
```

A, B, C… are commits. C and D were made on the branch; E brings them into master.

**Checkout / switch** = move to a different branch. Your files change to match that
branch. (Commit or set aside your changes first — Git will warn you.)

**Branch names:** short, lowercase, words joined with hyphens: `add-dcf-model`,
`fix-revenue-gap`.

## 6. Merging and rebasing

Both are ways to combine work from two branches.

- **Merge** — joins the two histories with a "merge commit". Simple and safe. **This is
  what we'll normally use**, usually by clicking the Merge button on GitHub.
- **Rebase** — replays your branch's commits on top of the latest master, as if you'd
  started from there. Gives a tidier, straight-line history, but rewrites commits.

**Rule of thumb:** use merge for now, rebase canbe a bit more complicated.0

### Merge conflicts

If we both changed **the same lines of the same file**, Git can't decide which version
to keep — that's a **conflict**. It's normal, not an error. Git marks the file and asks
you to choose. PyCharm shows a three-panel window: *yours* (left), *theirs* (right),
*result* (middle) — click the arrows to pick changes, then **Apply**. Pulling often and
keeping branches short makes conflicts rare.

## 7. Pull requests (PRs)

> "I raised a PR" = "I've finished some work on a branch and I'm asking you to review it
> before it goes into master."

A **pull request** is a page on GitHub that shows:

- which branch wants to be merged into which (e.g. `knowledge-base-plus-plan` → `master`),
- a description of the change,
- every line added (green) and removed (red),
- a discussion thread for comments and questions.

### The PR lifecycle

1. Create a branch, make commits, **push** the branch.
2. On GitHub, **open a pull request** (GitHub usually shows a yellow "Compare & pull request" banner right after you push).
3. The other person **reviews**: reads the changes, leaves comments, approves.
4. Make more commits on the same branch to address comments — they appear in the PR automatically.
5. Click **Merge pull request**. The branch's work is now in master.
6. Delete the branch (GitHub offers a button) and **pull** master locally.

### How to review a PR on GitHub

1. Go to the repo → **Pull requests** tab → click the PR. (You'll also get an email.)
2. **Conversation** tab: the description and discussion.
3. **Files changed** tab: every change. Hover over a line and click the blue **+** to comment on it.
4. For Markdown (`.md`) files, click the **document icon** ("Display the rich diff") at the top-right of the file to see it formatted instead of as raw text.
5. Click **Review changes** (top-right) → choose **Comment**, **Approve**, or **Request changes** → **Submit review**.

## 8. Reading files on GitHub

- Open the repo page → click any folder/file to browse.
- **Markdown files (`.md`) are shown formatted automatically** — headings, tables, bold, links. The `README.md` of each folder is displayed below the file list.
- At the top of a file there are **Preview / Code / Blame** buttons: *Preview* = formatted, *Code* = raw text, *Blame* = who last changed each line.
- To see files on a different branch, use the **branch dropdown** (top-left, says `master`) and pick the branch.
- **Commits** (clock icon, "N commits") shows the history; click one to see exactly what changed.

> Inside PyCharm, opening a `.md` file shows a split view: raw text on the left,
> formatted preview on the right (toggle with the icons at the top-right of the editor).

## 9. Doing it all in PyCharm

PyCharm has Git built in — you rarely need the command line.
(Shortcuts: **macOS** / **Windows-Linux**.)

### First time: get the project

**File → New → Project from Version Control** (or *Clone Repository* on the welcome
screen) → paste the repo URL → choose a folder → **Clone**.

### The branch widget

Top-left of the window, next to the project name, shows the **current branch**. Click it to:

- see local and remote branches,
- **New Branch…** to create one,
- click a branch → **Checkout** to switch,
- **Update** (pull), **Push**, **Merge into current** etc.

### Commit tool window — `⌘0` / `Alt+0` (or `⌘K` / `Ctrl+K`)

The left-side **Commit** panel lists your changed files:

- **Changes** = tracked files you modified; **Unversioned Files** = new files.
- **Tick the checkbox** next to a file to include it (that's staging).
- Double-click a file to see a **diff** (before vs after, side by side).
- Type a **commit message** at the bottom.
- **Commit** saves locally; **Commit and Push…** does both in one go.
- Right-click a file → **Rollback** to throw away your changes to it (careful — can't undo).

File-name colours in the project tree: **blue** = modified, **green** = new and added,
**red** = new and not added, **grey/olive** = ignored.

### Push — `⌘⇧K` / `Ctrl+Shift+K`

Shows the commits about to be uploaded and to which branch. Click **Push**.

### Pull — `⌘T` / `Ctrl+T` ("Update Project")

Choose **Merge** when asked how to update. Or **Git menu → Pull…**.

### Fetch

**Git menu → Fetch**, or the fetch icon in the Git tool window.

### Git tool window — `⌘9` / `Alt+9`

Bottom panel, **Log** tab: a picture of the history.

- Left: list of branches. Middle: commits as a graph (coloured lines = branches). Right: files changed in the selected commit.
- Click a commit to see what it changed; double-click a file for the diff.
- Right-click a commit for more actions (create branch from here, etc.).

### Who changed this line?

Right-click the line numbers in the editor → **Annotate with Git Blame**.

### Pull requests from PyCharm

The **Pull Requests** tool window (left sidebar, GitHub icon — or **Git → GitHub → View Pull Requests**)
lists the repo's PRs. You can open one, read the diff, comment and approve without leaving
PyCharm. First time, it asks you to log in to GitHub (**Settings → Version Control → GitHub**).

## 10. Everyday workflow (cheat sheet)

| Step | PyCharm | Command line |
|---|---|---|
| 1. Get latest master | Branch widget → `master` → Checkout; then `⌘T` | `git switch master` then `git pull` |
| 2. Start new work | Branch widget → New Branch… | `git switch -c my-branch` |
| 3. Edit code, run, test | — | — |
| 4. See what changed | Commit window `⌘0` | `git status`, `git diff` |
| 5. Stage + commit | Tick files, write message, Commit | `git add <files>` then `git commit -m "..."` |
| 6. Push branch | `⌘⇧K` | `git push -u origin my-branch` |
| 7. Open PR | GitHub website banner, or PyCharm Pull Requests window | — |
| 8. After merge | Checkout `master`, `⌘T`, delete old branch | `git switch master`, `git pull` |

## 11. Golden rules

1. **Pull before you start**, push when you finish.
2. **Never commit directly to master** — use a branch and a PR.
3. **Small, frequent commits** with clear messages.
4. **Never commit secrets** (passwords, API keys, the `.env` file).
5. **Don't "force push"** unless you're sure what you're doing.
6. **When stuck, don't panic** — committed work is almost never lost. Ask before deleting anything.

## 12. Quick glossary

| Term | Meaning |
|---|---|
| Repository (repo) | A project folder tracked by Git. |
| Clone | Copy a remote repo to your computer for the first time. |
| Commit | A saved snapshot of changes, with a message. |
| Stage / add | Mark changes to include in the next commit. |
| Push | Upload your commits to GitHub. |
| Fetch | Download news from GitHub without changing your files. |
| Pull | Fetch + apply the changes to your files. |
| Branch | A separate line of work. |
| Checkout / switch | Move to another branch. |
| Merge | Combine one branch's work into another. |
| Rebase | Replay your commits on top of another branch (tidier history). |
| Conflict | Both people changed the same lines; you choose which to keep. |
| Pull request (PR) | A request on GitHub to review and merge a branch. |
| Origin | The default name for the remote repo on GitHub. |
| master / main | The main branch. |
| HEAD | "Where you are now" — the current commit on the current branch. |
| Diff | The difference between two versions of a file. |
| .gitignore | List of files Git should never track. |
| Fork | Your own copy of someone else's GitHub repo (we don't need this — we're both collaborators on the same repo). |
