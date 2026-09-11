# Hormozi Advisor for Codex

Get a second set of eyes on your business.

Use this skill to review an offer, fix weak copy, spot what slows growth, or choose your next move. It uses Alex Hormozi's published teaching and your business facts. It gives direct advice in plain words.

## Start here

Open Codex in the folder where you work on your business. Paste this:

```text
Set this up for me: https://github.com/WavesCapital/hormozi-skills

Read the README and docs/install.md. Use Codex's Skill Installer to install
skills/hormozi, including its source library. Check that it works.
Then use $hormozi to help me set up my business context.
Use my existing BUSINESS.md if I have one. If not, ask me a few questions
at a time and help me draft one. Do not mark it approved without my approval.
```

You do not need to run code yourself. Codex can do the setup. If you share only the link, the page tells your agent where to start; include “set this up” to make your intent clear.

**Allow space for the sources.** The full skill includes about 2.4 GB of source files as of September 11, 2026. The download may take a while, and setup needs extra space for temporary files. You need Codex, internet access for installation, and Python 3.10 or newer for the bundled checks. Normal use needs no separate API key, CRM account, or paid data tool.

For Codex: the package is **`skills/hormozi`**, not the whole repo and not just `SKILL.md`. Follow [the setup guide](docs/install.md). Do not copy the author's business facts or machine paths into the user's setup.

## Make it know your business

`BUSINESS.md` is a short guide to your business, saved in your own business folder—not inside this skill.

Keep the basics there: what you sell, who buys, your offer, how you make money, and your next goal. Link to the files or tools that hold changing facts, such as prices, sales numbers, meeting notes, and your CRM.

This keeps advice personal without making you rewrite the file every week.

If you have no file, Codex helps you build one through a short talk. It asks a few questions, uses facts you already gave it, and marks gaps as unknown. You review the draft. It can still help before every section is done.

Your business file stays yours. Installing or updating the skill does not upload it to this repo. The skill changes it only when you ask. Keep passwords and private customer records out of it.

## Use it

After setup, try one of these:

- “Use $hormozi to review this offer. What would you change?”
- “Use $hormozi to make this email clear and easy to read.”
- “Use $hormozi to find our main limiting factor.”
- “Use $hormozi to challenge this plan before we spend money.”

Add the plan, copy, or facts you want reviewed. Ask follow-up questions as you would with an advisor on your team.

The skill uses private role-play based on Hormozi's teaching. It is not Alex Hormozi, is not endorsed by him, and does not invent his quotes or personal stories. Copy meant for customers stays in your voice.

## What you get

- One advisor for offers, leads, sales, profit, customer results, and teams.
- Plain answers that fit your question—not a long form every time.
- Source guides, saved text, transcripts, page images, and search tools.
- Links to the checked page or video time when advice relies on a source.
- Templates for offers, sales reviews, experiments, and business context.

## What is not automatic

Installing does not connect your CRM, send messages, create a daily video job, or change your Codex model. Those need their own setup and permission.

The library is a saved collection, not a live feed. Some original files and prepared video visuals are not in this release. If a source is missing, the agent must say so and limit that claim—not pretend it checked it. The larger source-by-source audit is still in progress.

## Setup help and updates

- [Install, check, update, or fix the setup](docs/install.md)
- [What changed in the Astra update and what was tested](docs/astra-upgrade.md)
- [How the advisor works](docs/architecture.md)
- [Source access and rights](docs/source-policy.md)
- [Optional YouTube sync](docs/youtube-sync.md)
- [File map for agents](llms.txt)

The [MIT license](LICENSE) covers our original framework and docs. Books, transcripts, and other third-party sources keep their own rights. Access to this repo does not grant rights to republish them.
