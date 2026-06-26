# Dispatch briefs

Fill-in templates for the three research jobs in `crank-refine` (see SKILL.md → Subagents & research). Read this file when you're about to brief a research subagent at Flow step 3; pick the brief that matches the job and fill the `<…>` slots.

## Explore the codebase

> Explore `<area or claim>` in this codebase. We're refining a `<brainstorm/spec/plan>` for `<one-sentence summary>`.
>
> Report:
>
> - whether the surface or pattern in question exists, and the `file:line` where it lives (or "not found");
> - one or two existing features that do something analogous, and the convention each follows (`file:line`);
> - any canonical helper, module, or pattern an implementer would be expected to reuse for this (`file:line`).
>
> Don't propose a design — surface what exists and what's true. If a claim I'm checking is wrong, say so plainly.

## Research an approach (web search in scope)

> Research `<question>` to inform a decision in a `<brainstorm/spec/plan>`. We're weighing `<the options on the table>`.
>
> Report:
>
> - the leading approaches or libraries, and for each what it optimizes for and its main trade-off;
> - how comparable projects solve this, with a source link each;
> - a recommendation for our context (`<one line of constraints>`) and what it gives up.

## Check current facts (latest versions, current docs)

> Find the current fact for `<package / API / tool>` to ground a recommendation in a `<brainstorm/spec/plan>`. The artifact assumes `<assumption being checked>`.
>
> Report:
>
> - the latest stable version and its date, or the current shape of the API;
> - whether `<the artifact's assumption>` still holds today;
> - the canonical documentation link.
>
> Prefer a documentation MCP (e.g. **context7**) for library or framework docs; use web search otherwise.
