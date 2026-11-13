# FlashFree

FlashFree is a static English–Vietnamese vocabulary flashcard app. The front of a card is the English word; the back is the Vietnamese gloss and a short example. Progress stays in this browser.

Open it at [https://tuanlmogle.github.io/flashfree/](https://tuanlmogle.github.io/flashfree/) after GitHub Pages is enabled.

## Study

On a first visit, levels **B1** and **B2** are already selected. Choose any mix of A1, A2, B1, B2, and C1, then start.

- Tap a card to flip it.
- **Biết** marks the word as known. **Chưa biết** keeps it in the pile.
- Swipe right for Biết and left for Chưa biết.
- Reload the page and the same marks are still there. **Thống kê** shows counts for the selected decks and for each level.
- **Nguồn** credits the word list and the typeface.

## Run locally

From this directory:

```bash
python3 -m http.server 8080
```

Then open `http://127.0.0.1:8080/`.

Links to CSS, JavaScript, fonts, and `data/vocab.json` are relative to the page. The same files work at the server root, under `/flashfree/`, and on a custom domain. If the address has no trailing slash and no filename, the page adds the slash before those files load.

## Rebuild the word list

`scripts/build_vocab.py` writes `data/vocab.json`.

```bash
python3 scripts/build_vocab.py
python3 scripts/build_vocab.py --check
```

## GitHub Pages

The workflow `.github/workflows/pages.yml` publishes this repository with `actions/upload-pages-artifact` and `actions/deploy-pages` on every push to `main`.

After the workflow file is on `main`, set **Settings → Pages → Source** to **GitHub Actions** once. The site is then `https://tuanlmogle.github.io/flashfree/`. No paid host and no custom domain are required.

## Credits and license

Word-list notes are in [DATA_SOURCES.md](DATA_SOURCES.md). Application code is under the [MIT license](LICENSE). Be Vietnam Pro is under the SIL Open Font License in `fonts/OFL.txt`.
