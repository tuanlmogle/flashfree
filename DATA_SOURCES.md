# Data sources

## Vocabulary

The English headwords, IPA, parts of speech, Vietnamese glosses, and example sentences in `scripts/build_vocab.py` (compiled to `data/vocab.json`) were written for FlashFree.

CEFR-style labels A1, A2, B1, B2, and C1 are approximate study bands so a learner can pick a deck. They are not the Cambridge English Vocabulary Profile, and the list is not the Oxford 3000/5000 or any other publisher word list.

Each card has:

- `id`, `en`, `ipa`, `pos`
- `vi` — a short Vietnamese gloss
- `example`, `exampleVi` — an original example pair
- `level` — one of A1, A2, B1, B2, C1

Rebuild with `python3 scripts/build_vocab.py`.

## Typeface

Be Vietnam Pro, copyright 2021 The Be Vietnam Pro Project Authors ([bettergui/BeVietnamPro](https://github.com/bettergui/BeVietnamPro)), is bundled under the SIL Open Font License 1.1. The license text is `fonts/OFL.txt`. The reserved font name stays Be Vietnam Pro; these files are unmodified.

## What this app does not use

FlashFree does not call a dictionary API, a paid font host, or an account service. Study marks are stored only in the browser under the localStorage key `flashfree.v1`.
