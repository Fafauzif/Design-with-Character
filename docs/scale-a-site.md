# Taking one idea across a large site

A returning visitor has already seen the entrance. Give them a short path to the task they came back for. A first-time visitor still needs to recognize the collection, the performer, the object or the place. Plan those arrivals separately.

## Design the site by jobs

Work outward from real URLs, content and tasks. Keep a route **family** for pages that share a job and behavior. A thousand recording pages can use one detail layout. A checkout, an interview transcript and a listening queue usually need different treatment. Map actual entry links, likely exits, browser Back behavior, and whether an action should persist.

| Record one decision for each family | What the decision controls |
|---|---|
| Visitor and task | What someone must understand or do on arrival |
| First screen and dominant object | Where the visitor looks, and which part actually belongs to this subject |
| Next action and resulting state | What visibly changes, including focus or a spoken status where appropriate |
| Repeated conventions | Words for common actions, navigation order, focus treatment, saved-state feedback |
| Permitted variations | Information density, use of negative space, the role of imagery, time spent in motion |
| Edge examples | Long names, empty collections, a failed import, direct deep links, missing art or partial data |
| Return route | A quick way to resume, undo, compare, or go back to the original context |

Sketch three neighboring pages from the visitor's route. Mask the copy and color. If each resolves to a title, a square picture and the same pile of boxes, compare their actual jobs. A product family with matching jobs can share a composition. If the jobs differ, change the relationship between the content and the visitor's action before choosing more colors.

## Build an honest slice

1. Pick a frequent journey, a deep-link arrival, and a recovery path where a visitor could lose work. Include one real difficult content example. When a brief only needs one screen, use states on that screen.
2. Prototype the quietest useful version of each. Place artwork once the reading order, input and result make sense with the art removed. Spend the art budget where it changes what visitors understand.
3. Implement the shared shell early. Give links readable names, controls visible focus, and key destinations ordinary addresses. Confirm the main route works under a repository subpath and when a visitor lands in the middle.
4. For a large collection, review at least one real screen per **family**, and the most demanding content variant within it. Inspect content extremes by locale or data length. Keep an inventory of unexamined combinations. On later changes, revisit the affected family, its neighbors in the main journey, and all places that consume a changed shared component.
5. Compare resting, active, completed, empty and failed states **where each can actually occur**. At narrow width, scroll through the action, commitment and feedback together. Check keyboard focus after content disappears. Trigger motion twice quickly and revisit with reduced motion enabled.

## Optional local tools

Run these from the kit directory. Set the target folder to the website you are designing. The commands below use an example relative path; double quotes also work for paths containing spaces.

```sh
python scripts/project.py --project "../my-site" init
python scripts/project.py --project "../my-site" check
python scripts/project.py --project "../my-site" walk
python scripts/project.py --project "../my-site" record "Only the active reel expands into a transcript" --because "Returning listeners resume at a spoken phrase"
python scripts/project.py --project "../my-site" moves
```

`init` creates `site-plan.json`. Fill its empty fields before running `check`. Use document-relative examples from the site's publication root, such as `films/morning.html` or `collection.html?q=wind`. Group additional URLs that share a family in its `examples` list. Each named journey must start and end in the expected family and state its observable result. A one-screen site can have a one-family journey. `walk` prints a compact brief for a reviewer to exercise. For a static export, pass `check --site PATH` to confirm representative files exist. Dynamic route resolution still needs a running-site test.

`moves` reads only the current project's `.design-moves/` directory. `record` saves one decision and one reason. This kit ignores that directory in Git. In another project, add the same ignore rule if you want records to stay local. Keep records where they would help someone choose differently next time. A missing history is an invitation to use the brief, without assuming past preferences.

A passing check validates the plan's structure, coverage and optional local files. It cannot tell whether a planned page actually looks or behaves as described. For a reference plan you can execute now, use the commands below.

```sh
python scripts/project.py --project examples/weather-project check --site weather
python scripts/project.py --project examples/weather-project walk
```

For a running site, use the general-purpose visitor runner. Point it at a local preview and a project plan. Add an optional `browser-journeys.json` alongside the plan for actions and on-screen assertions specific to that website. Limit a large run to one family while working, then cover all families for a release. The [browser check guide](checking-the-release.md) documents the inputs and limits.

```sh
python scripts/visit_project.py --project examples/weather-project --base-url http://127.0.0.1:8000/weather/ --only-family comparison
```
