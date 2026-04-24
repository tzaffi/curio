# Curio Translation

## Purpose

Define the normative v1 translation behavior used during Curio dossier assembly.

This document is normative for:

- when Curio decides a text block needs translation
- how English is defined for translation purposes
- where translated text is stored in the persisted payload
- how translated blocks relate to original `dossier_snapshot.evidence_text` blocks
- how translated and non-translated blocks are identified

This document is not the place to define:

- the Google Sheets workbook model
- the detailed JSON payload contract outside translation behavior
- model or provider selection for language detection or translation
- prompt wording or downstream evaluation policy

Those belong in [SCHEMA.md](/Users/zeph/github/tzaffi/curio/SCHEMA.md), [JSON-PAYLOAD.md](/Users/zeph/github/tzaffi/curio/JSON-PAYLOAD.md), and future implementation docs.

## Design Principles

The v1 translation workflow should follow these rules:

- Translation is a dossier-preparation step, not an evaluation-output step.
- Translation target is always English.
- Translation operates per human-readable dossier text block.
- Original text remains preserved in the dossier when translation occurs.
- Translated English text belongs in `dossier_snapshot.evidence_text` because it is evaluator input.
- Translation does not belong in `evaluation`.
- Curio translates the full normalized source block before any dossier-size truncation.
- `dossier_snapshot.evidence_text` remains an ordered list, not a keyed object.

## Human-Readable Text Blocks

For translation purposes, a human-readable text block is an `evidence_text` entry intended for semantic evaluation.

This includes blocks such as:

- `tweet_text`
- `page_main_text`
- `repo_readme`

This does not include metadata-only values stored in `dossier_snapshot.details`.

## English Classification

Curio must perform language detection on each human-readable text block before evaluation.

A block counts as English only when all of the following are true:

- the detected language code is `en` or starts with `en-`
- the detector confidence is at least `0.90`

All other blocks must be translated to English before evaluation, including:

- non-English blocks
- mixed-language blocks
- ambiguous blocks below the confidence threshold

## Translation Workflow

For each human-readable dossier text block, Curio must:

1. assemble the normalized source-language text block
2. detect the block language
3. assign the original block a unique numeric `block_id`
4. if the block counts as English, keep only the original block
5. otherwise translate the full normalized block into English
6. append the translated English text to `dossier_snapshot.evidence_text` as a paired block that references the original block by `translation_of`

## Dossier Representation

`dossier_snapshot.evidence_text` remains an ordered array because it represents the ordered text shown to the evaluator.

Each block must carry:

- `block_id`
- `name`
- `language`
- `translation_of`
- `text`
- `was_truncated`
- `original_char_count`

When Curio translates a block:

- the original block remains present with `translation_of = null`
- the translated block contains the exact English text shown to the evaluator
- the translated block uses `language = en`
- the translated block uses the original name plus `_en`
- the translated block stores the original block's `block_id` in `translation_of`
- the translated block appears immediately after the original block in `dossier_snapshot.evidence_text`

When Curio does not translate a block:

- the original block remains present with `translation_of = null`
- the block's own `language` field records the detected language
- absence of a paired translated block means the original block was treated as English

Examples:

- `tweet_text` -> `tweet_text_en`
- `page_main_text` -> `page_main_text_en`
- `repo_readme` -> `repo_readme_en`

English blocks remain unpaired in v1.

## Out Of Scope

This document does not define:

- which language detector Curio uses
- which translation model or service Curio uses
- batching or caching strategy
- downstream model behavior after dossier assembly
