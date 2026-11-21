# Direct a large site

Start with one visitor's round trip. A title, primary button and next route rarely cover arrival from search, returning to edit, or recovering after a lookup fails.

## Route map before components

For each route **family**, record its audience/task, primary content, entry/deep link, next/return action, what survives navigation, the narrowest useful composition, and any meaningful empty/error/long-content state. Group equivalent records under one detail template. Distinguish different tasks that happen to share a URL or component. For a migration, map old external destinations and preserve or redirect them deliberately.

| Family in a fictional weather collection | Composition tied to the job | Acceptance test |
|---|---|---|
| Entrance | A single cabinet silhouette makes the collection tangible. | A first-time visitor identifies an opening; a returning visitor can go straight to the inventory. |
| Browse and search | A compact index gives names and differences equal reading priority. | Clear an empty query result without losing the collection. Back from a result restores the user's route context. |
| Specimen | One object occupies the stage; observations sit next to the corresponding feature. | A direct URL explains what was found, and supports returning, comparing or recording a note. |
| Compare | Shared measurements line up on a common baseline. | Change one specimen and keep the other in view. On a phone, labels stay attached to values. |
| Notebook | The saved observation becomes the content; editing takes precedence over spectacle. | Reopen on the supported origin, recover existing work, and show a usable outcome when storage is unavailable. |
| Missing entry | A short message identifies the loss and offers a useful destination. | Open it directly; the escape works under the deployment base path. |

This map illustrates a method. A recital program could need time conflicts, a performer page and a seat-access route; an extension may split sparse popup controls from a long-lived dashboard. Choose the project's actual families.

## Define what repeats

Keep stable the language for common actions, link and focus behavior, landmarks, reading type, state conventions and return paths. Reuse the same detail skeleton for sibling records when visitors need to compare them. Choose the first focal point, content scale, density, viewing angle, traversal and amount of choreography per family. A button that saves always has the same meaning. A return visit to compare items should let the visitor bypass the opening performance entirely.

Turn these decisions into small, maintainable pieces: shared navigation, focus treatment, tokens, and data rendering where their behavior matches. Let route templates own different markup and content hierarchies. Derive URLs and links from the site's own routing approach; test bookmarks and hosting under a subpath. Avoid scattering separate implementations of the same persistence or state logic across art-directed pages.

Decide which state belongs in a shareable URL. A public specimen ID or an agreed public filter can travel in a link. A reader's private field note, draft message, account token or identifying detail should stay out of URLs, including fragments and automatic return parameters. Use the project's intended private storage for these values. If the brief calls for sharing user-authored content, give the author a deliberate share action and show what is included. Test a copied deep link using a second session with empty storage. Confirm it opens the intended public state and reveals only material appropriate for that recipient.

## Judge a sequence, not a cover

Build the entrance, an ordinary deep link and a demanding task before multiplying pages. Inspect first screens together in reading order. Then compare one changed or failure state per family at phone width. If cards, hero proportions or action placement repeat on unrelated tasks, change the underlying information order. If every family uses a different symbol for the same action, unify that symbol. Test a route that skips the homepage and a route in reverse. Add representative long titles, duplicate names, content gaps and late-arriving images where the product can encounter them. Correct the family template, rerun the affected routes, and keep deliberate exceptions close to their content.
