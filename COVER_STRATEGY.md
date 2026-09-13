# Research cover strategy

A cover must explain what a reader will find in the repository at a glance.
Use the original networking research cover as the communication reference:
identify the field, state the question or idea, and explain the contribution.

## Message hierarchy

1. **Field:** `AI INFRASTRUCTURE RESEARCH` on every cover.
2. **Headline:** a short, specific research question or central idea, with deliberate
   line breaks. The networking cover retains “Network capacity is sometimes compute capacity.”
3. **Offering:** one concise sentence naming the actual artifact: a simulator,
   decision model, standard, validator, architecture, or portfolio of frameworks.
4. **Illustration:** one supporting technical relationship, subordinate to the copy.

The portfolio cover reads “Usable Compute” and “AI infrastructure models,
standards, and decision frameworks.” Each project cover explains its own contribution.

## Copy accuracy

Read the repository's README before drafting. Preserve distinctions between a
research model and a deployed system, between an architecture and a running
controller, and between a specification linter and tests of physical hardware.
Use the artifact the repository actually provides as the offering sentence.

Do not put performance percentages, cost savings, benchmark wins, production
claims, or certification promises on these covers. Their context belongs in the
research. Do not add marketing superlatives or imply that physical equipment is for sale.

Store the exact field label, headline, description, font size, and line breaks in
each repository's `assets/covers/copy-v2.json`. Its README commit identifies the
source used for the wording. Proofread this copy before rendering.

## Visual execution

Give most of the canvas to readable text on a dark blue-charcoal background.
Use warm-white headlines, a muted teal field label, and a quieter description.
Keep technical linework to the right, with restrained teal and ochre accents.
Use generous margins and simple layouts that also work at thumbnail size.

Do not embed DIMAGGI names or logos, author names, dates, watermarks, luminous
neon effects, decorative particles, or glossy product-display imagery.

Generate the supporting illustration with the built-in image tool. Generate no
lettering in that layer. Typeset the exact copy separately with the checked-in
Swift renderer, using actual Arial fonts. The renderer rejects text that exceeds
its allocated width instead of silently cropping or shrinking it.

## Checks before publishing

- Compare wording with the README and proofread it for spelling and meaning.
- Verify that the final headline and offering match the copy file; use OCR as
  an additional check and review ambiguous glyphs visually.
- Inspect every cover at full size and in a thumbnail contact sheet.
- Check margins, line breaks, contrast, and separation from the illustration.
- Export GitHub JPEGs at 1280 × 640 and LinkedIn JPEGs at 1200 × 627, below 1 MB.
- Update the portfolio website's sharing image to the current version.
- Upload each GitHub image through its Social preview settings. Download the
  resulting public preview and compare its SHA-256 with the prepared JPEG.

Keep earlier versions available. A new file committed to Git does not replace
the image already configured in GitHub's Social preview settings.

## Files and reuse

[Browse current covers and copy](COVER_ARTWORK.md). Each repository retains its
finished PNG master, separate illustration, exact copy, and illustration prompt.

To render from a copy file on macOS with Swift and Arial installed:

```sh
swift tools/cover_artwork/render.swift /path/to/repository/assets/covers/copy-v2.json
```

Paths inside the copy file resolve relative to that file. Rendering creates the
three v2 exports beside it and does not regenerate the illustration.
