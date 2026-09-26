# Issue tracker: GitHub

Issues and specs live in caw1517/DCSRecorder on GitHub.
Use the gh CLI with --repo caw1517/DCSRecorder.

## Operations

- Create: gh issue create --repo caw1517/DCSRecorder --title "..." --body-file <file>
- Read: gh issue view <number> --repo caw1517/DCSRecorder --comments
- List: gh issue list --repo caw1517/DCSRecorder --state open
- Comment: gh issue comment <number> --repo caw1517/DCSRecorder --body-file <file>
- Label: gh issue edit <number> --repo caw1517/DCSRecorder --add-label "..."
- Remove label: gh issue edit <number> --repo caw1517/DCSRecorder --remove-label "..."
- Close: gh issue close <number> --repo caw1517/DCSRecorder --comment "..."

For multiline bodies, write the content to a temporary file and use --body-file.
Fetch labels and comments when evaluating an issue.

“Publish to the issue tracker” means create a GitHub issue.
“Fetch the relevant ticket” means read the issue and its comments.

## Pull requests as a triage surface

PRs as a request surface: no.

## Wayfinding

Use one issue labelled wayfinder:map for Notes, Decisions-so-far, and Fog.
Link child tickets as GitHub sub-issues, or use a task list in the map
and a “Part of #<map>” reference in each child.

Label children wayfinder:research, wayfinder:prototype,
wayfinder:grilling, or wayfinder:task.

Record blockers using native GitHub issue dependencies when available;
otherwise use a “Blocked by: #<number>” line in the child.
A ticket is unblocked when all blockers are closed.

Select the first open, unblocked, unassigned child in map order.
Claim it by assigning yourself before starting work.
Resolve it by commenting with the answer, closing it, and adding
a summary and link to the map's Decisions-so-far.
