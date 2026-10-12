---
name: dated-items-list-content
description: Use when editing dated items or lists on experience.html.
category: web-content
---

Dated lists on this site are `<ul class="items">` with one `<li>` per entry: a `.date` column and a `.body` holding the name link and a `.meta` line. Use exactly this structure in every dated list, as CLAUDE.md requires.

- Order newest first. Dates read "Mon YYYY", or "Mon &ndash; Mon YYYY" for a span.
- A specialization is one entry. Fold its courses under it rather than listing each course as a separate row, and say in the reply which courses were folded.
- Where the source gives no issuer, do not present an invented one as fact. Name each unverified issuer in the reply so the user can check it.
- Add a new section with an `<h2>` and keep CLAUDE.md's File Structure line for that page in sync.
