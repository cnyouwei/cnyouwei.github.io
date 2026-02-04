# Static website (redesigned)

This ZIP contains a consolidated, single-page academic website built from the provided source pages.

## What changed

- Consolidated `index.html`, `bio.html`, `teaching.html`, `talks.html`, `students.html` into **one** `index.html`.
- Kept the old page filenames as **redirect stubs** to the corresponding tab in `index.html` for backward compatibility.
- Removed heavy dependencies (Bootstrap/AOS/FontAwesome) and replaced with a lightweight custom CSS + vanilla JS.
- Added a responsive fixed navigation bar and a paper filter/search UI on the Research tab.

## Files & folders

- `index.html` — main site
- `css/site.css` — styles
- `js/site.js` — navigation + filters
- `assets/avatar.png` — placeholder avatar
- `papers/` — placeholder PDFs for links that existed in the HTML but were not present in the ZIP you provided

## Replacing placeholders

If you have the real CV / slides / paper PDFs, just replace the corresponding file in:

- `CV.pdf`
- `papers/*.pdf`

No other changes are required.
