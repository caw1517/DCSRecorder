# Writing a brief that Claude Design handles well

Researched 2026-10-13 for #49 (part of map #47, feeds #58 "Write the Claude Design brief").
Scope: Anthropic's Claude Design product, as documented by Anthropic itself. Third-party guides and press coverage were read only to find primary pages; no claim below rests on them.

## Sources

| Key | Source | Owner / trust |
| --- | --- | --- |
| [HC-start] | [Get started with Claude Design](https://support.claude.com/en/articles/14604416-get-started-with-claude-design) | Anthropic Help Center, current |
| [HC-ds] | [Set up your design system in Claude Design](https://support.claude.com/en/articles/14604397-set-up-your-design-system-in-claude-design) | Anthropic Help Center |
| [HC-migrate] | [Migrate from standalone Claude Design to Claude](https://support.claude.com/en/articles/17440474) | Anthropic Help Center |
| [Launch] | [Introducing Claude Design by Anthropic Labs](https://www.anthropic.com/news/claude-design-anthropic-labs), 2026-04-17 | Anthropic announcement |
| [Academy] | [Using Claude Design for prototypes and UX](https://academy.claude.com/tutorials/using-claude-design-for-prototypes-and-ux) | Anthropic Claude Academy tutorial |
| [Blog] | [How the product designer who built Claude Design uses it](https://claude.com/blog/how-the-product-designer-who-built-claude-design-uses-it-to-explore-ideas-before-building-them) | Anthropic blog; one designer's practice, not formal docs |
| [CC-cmds] | [Claude Code commands reference](https://code.claude.com/docs/en/commands) (`/design`, `/design-sync`) | Claude Code docs |
| [CC-art] | [Claude Code artifacts docs](https://code.claude.com/docs/en/artifacts) (Draft a design canvas, Page constraints) | Claude Code docs |

## 1. What Claude Design is

- An Anthropic Labs product, launched 2026-04-17 as a research preview on Claude Opus 4.7, for making designs, prototypes, slides and one-pagers by describing them and refining through conversation. [Launch]
- It is now part of Claude itself: new designs and design systems are stored as **artifacts**. The standalone site `claude.ai/design` closes **2026-12-14**; chats and comments left there are deleted then. [HC-migrate]
- Entry points: ask for a design in a chat (or Output > Design), pick the Design template on the Artifacts tab, or run `/design [brief]` in Claude Code. Available on Free, Pro, Max, Team and Enterprise; on Enterprise it is on by default from 2026-10-15. [HC-start] [CC-cmds]
- The workspace is a chat panel plus a canvas of **artboards**. Refinement is by chat (structural changes), inline comments on an element (targeted fixes), and direct canvas editing (drag, resize, text, colour). [HC-start] [CC-art]
- It is positioned for ideation and buy-in, not shipping code: "Production software belongs in Claude Code." It has no image model, so it cannot generate logos. [Blog]

## 2. Inputs it accepts

| Input | Status | Source |
| --- | --- | --- |
| Text prompt / brief | Yes. Describe goal, layout, content, audience; Claude may ask clarifying questions. `/design` takes the brief as its argument. | [HC-start] [CC-cmds] |
| Screenshots, wireframes, competitor shots, existing assets | Yes. A photo of a paper sketch works for layouts that are hard to describe. | [HC-start] [Blog] |
| Documents | Yes: DOCX, PPTX, XLSX, PDF; decks/docs can donate a visual style. | [Launch] [HC-ds] |
| Web capture | Yes, a tool that grabs elements from an existing website. | [Launch] |
| Codebase | Yes: link a GitHub repo or attach a local directory. Claude reads components, styling, framework patterns and file layout. Large repos lag; scope to the relevant package, exclude `.git`/`node_modules`. | [HC-start] [Academy] |
| Design system | Yes (beta): from chat (brand files, Figma files, decks, logos, fonts) or from Claude Code `/design-sync`, which converts a **React** component library. Output is checked against it. | [HC-ds] [CC-cmds] |
| Multi-screen flows | Yes, described in words: "Walk Claude through the journey and it will generate each screen in context." | [Academy] |

## 3. What it exports

- Export menu: `.zip`, PDF, PPTX, Google Slides, standalone HTML, a set of third-party tools (Canva, Gamma, Miro, Adobe tools, and site builders such as Lovable, v0, Replit, Vercel, Netlify, Wix; Figma is not listed), and **Handoff to Claude Code** (local agent or Claude Code Web). [HC-start]
- From the `/design` canvas in Claude Code, each artboard exports as PNG or PDF. [CC-art]
- **Handoff bundle:** the project's design files, the chat history and a README telling the coding agent how to read the designs, plus a prompt (with the bundle URL) to paste into Claude Code. The Academy screenshot shows that prompt asking the agent to implement `index_v2.html`. [Academy] [Launch]
- **Framework:** no official source names a framework for the output. What is documented points to **HTML/CSS/JS web prototypes** (standalone HTML export, an `index_v2.html` handoff target, artifacts being single HTML pages [CC-art]). The handoff is designed so Claude Code re-implements the design in the target codebase; it is a reference, not production code. [Academy] [Blog]

## 4. Brief length and structure

**Thin sources.** Anthropic publishes no guidance on brief *length*. Its own example prompts are one or two sentences ("Create an onboarding flow for a new user", five screens) [Academy]; the structured guidance is about *what* to include, not how much. The recommendations below combine what the sources say (cited) with inference (marked).

What the sources say:

1. **Cover goal, layout, content, audience.** [HC-start]
2. **State the platform.** Say whether it must work on mobile, tablet or desktop, or just one. [HC-start]
3. **Describe the whole journey:** entry point, each step in order, end state, with a screen count and the purpose of each screen. [Academy]
4. **Name the interactions** you need (e.g. a panel that slides in on click, keyboard shortcuts). [Academy]
5. **Specify the look**, or output drifts to Claude's recognisable default aesthetic: name fonts and colours, give a moodboard or real assets, or ask it to propose pairings. [Blog]
6. **Ask for empty, error and loading states** and different data volumes. [Academy]
7. **Think the brief through before opening the tool**; context up front beats a blank-canvas prompt. [Blog]
8. **Stage it:** core layout and content first, then interactions, edge cases, polish. [HC-start]
9. **Ask for 2-3 variations** when the direction is unsure (the designer asks for ten and keeps one or two). [HC-start] [Blog]
10. **Name components** (and keep names stable); names carry into the handoff. Record design decisions and their reasons in the chat, because the chat history goes into the bundle. [Academy]

Recommended shape for #58 (inference from the above):

- **One structured brief, a few pages at most**, organised as: purpose and audience; platform and window size (Windows desktop window, one fixed size, no browser chrome); visual direction; vocabulary (the CONTEXT.md user-facing terms, with forbidden words); a numbered **screen inventory** with one short block per screen (purpose, content, primary action, where it leads); the guided flows as ordered screen sequences; states (empty, error, loading, DCS-closed); developer mode as a delta on named screens; safety wording to keep verbatim.
- **Do not ask for everything in one turn.** Use the brief as the shared reference, but request the first pass as layout-only for the core flow (perhaps as wireframes, which the designer recommends for structure [Blog]), then add flows, states, delete/tidy and developer mode in later turns. This follows the staged guidance [HC-start] and limits token spend (see limits).
- **Upload reference material alongside the brief:** screenshots of the current companion UI, any sketches, and a small design system (colours, type, spacing) if a visual identity is decided.

## 5. Known limits to work around

| Limit | Workaround in the brief / process | Source |
| --- | --- | --- |
| Shares usage limits with chat and Claude Code; large codebases and many iterations cost more. | Don't link the whole repo; give a scoped brief; use direct canvas edits (no tokens) for small fixes. | [HC-start] [Blog] |
| **No version history yet.** | Ask Claude to save the current state before exploring a new direction; it says where. Export a `.zip`/PDF at accepted milestones. | [HC-start] |
| Inline comments may not appear; "chat upstream error". | Paste feedback into chat; open a new chat tab in the same project. | [HC-start] |
| Multi-person simultaneous editing is basic. | One person drives a design at a time. | [HC-start] |
| Design-system import is only as good as its source; `/design-sync` expects React components. | Our app has no React design system; describe the look in the brief or build a small system from chat. | [HC-ds] [CC-cmds] |
| Very large repos lag; Chrome struggles with big file trees. | Don't attach the DCS Recorder repo wholesale; it is not a UI codebase to reuse anyway. | [HC-start] [Academy] |
| Output is a web prototype, not a native desktop app. | State the target as a desktop window and treat the result as a reference for the build issues, not code to ship. | [Section 3] [Blog] |
| No logo generation. | Supply an icon/logo if wanted, or leave a placeholder. | [Blog] |
| Standalone `claude.ai/design` closes 2026-12-14; chats/comments there are deleted. | Work in Claude (artifacts) or `/design`, not the standalone site. | [HC-migrate] |
| Default aesthetic is generic. | Give explicit visual direction. | [Blog] |

## Where sources are thin

- **Brief length:** no official number or template; section 4's shape is inference.
- **Export framework and bundle format:** not specified beyond HTML files, chat history and a README.
- **Desktop-app specifics:** nothing official on native desktop chrome, window sizes or how many artboards one turn handles well.
- **Quantitative limits:** no stated caps on screens per project, upload size or file count (the design-system article says so explicitly [HC-ds]).
- The Help Center changes often (it moved from research preview, to beta, to "in Claude" within six months); re-check [HC-start] before writing #58.
