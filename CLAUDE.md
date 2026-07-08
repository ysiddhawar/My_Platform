# Project Instructions

## Skill Discovery System

This project has access to the `npx skills` ecosystem (skills.sh) for discovering and installing specialized AI agent skills.

When the user asks about finding a capability, extending my abilities, searching for a tool or workflow, or says things like "how do I do X" / "find a skill for X" / "is there a skill that can...", follow this process:

1. **Load** the installed skill discovery guide at `.agents/skills/find-skills/SKILL.md` for the full workflow.
2. **Check** the [skills.sh leaderboard](https://skills.sh/) for well-known skills.
3. **Search** with `npx skills find <query>` if the leaderboard doesn't cover it.
4. **Verify quality** — prefer skills with 1K+ installs and reputable sources (vercel-labs, anthropics, microsoft).
5. **Present** options to the user and offer to install with `npx skills add <package> -g -y`.
