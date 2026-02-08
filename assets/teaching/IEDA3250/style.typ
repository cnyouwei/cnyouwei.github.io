#import "@preview/frame-it:2.0.0": *
#import "@preview/gentle-clues:1.2.0": conclusion, experiment, idea, info, memo, question, success, warning
#import "@preview/ratchet:0.0.1": *
#import "@preview/mannot:0.3.1": *

#import "@preview/theoretic:0.3.0"
#import theoretic.presets.bar: proof //

#let date-str = datetime.today().display("[year]-[month]-[day]")

//Suppress numbering for equations
#let nonum = math.equation.with(block: true, numbering: none)

// Theme colors
#let accent-color = rgb("#003366")
#let accent-color-light = rgb("#003366").transparentize(20%)
#let pop-color = maroon

// frame-it presets
#let (definition,) = frames(
  definition: ("Definition",),
  base-color: rgb("#0e4f10"),
  kind: "definition",
)
#let (theorem,) = frames(
  theorem: ("Theorem",),
  base-color: rgb("f28482"),
  kind: "theorem",
)
#let (lemma,) = frames(
  lemma: ("Lemma",),
  base-color: rgb("883677"),
  kind: "lemma",
)
#let (proposition,) = frames(
  proposition: ("Proposition",),
  base-color: rgb("#609295"),
  kind: "proposition",
)
#let (example,) = frames(
  example: ("Example",),
  base-color: rgb("3282B8"),
  kind: "example",
)
#let (poll,) = frames(
  poll: ("Poll",),
  base-color: rgb("AF3E3E"),
  kind: "poll",
)

// Compare two locations robustly via absolute page position.
#let same-loc(a, b) = {
  a != none and b != none and a.position() == b.position()
}

// `none` and empty content `[]` are both treated as missing.
#let present(x) = x != none and x != []

#let join-titles(parts) = {
  let keep = parts.filter(present)
  if keep.len() == 0 { [] } else { keep.reduce((acc, p) => [#acc | #p]) }
}

// ---- helper: current heading *body* at a given level (1/2/3)
// Assumes it is called where context is already available.
#let current-heading(level: 2) = {
  let here-loc = here()
  let sel(l) = selector(heading.where(level: l))

  let curr(l) = {
    let parent = if l <= 1 { none } else { curr(l - 1) }
    let parent-loc = if parent == none { none } else { parent.location() }

    // 1) lag fix: prefer next heading on same page, scoped to same parent
    let after = query(sel(l).after(here-loc))
    if after.len() != 0 {
      for h in after {
        if h.location().page() != here-loc.page() { break }
        if parent-loc == none {
          return h
        } else {
          let p = query(sel(l - 1).before(h.location()))
          if p.len() != 0 and p.last().location() == parent-loc {
            return h
          }
        }
      }
    }

    // 2) fallback: last heading before here(), scoped within the parent
    let before = {
      if parent-loc == none {
        query(sel(l).before(here-loc))
      } else {
        query(sel(l).after(parent-loc).before(here-loc))
      }
    }

    if before.len() != 0 { before.last() } else { none }
  }

  let h = curr(level)
  if h == none { none } else { h.at("body") }
}

#let current-section-titles() = {
  join-titles((
    current-heading(level: 1),
    current-heading(level: 2),
    current-heading(level: 3),
  ))
}

// - 1 author: "A"
// - 2 authors: "A and B"
// - 3+ authors: "A et al."
#let author-name(author: auto) = context {
  let a = if author == auto { document.author } else { author }

  if type(a) == str {
    a
  } else if a.len() == 0 {
    ""
  } else if a.len() <= 2 {
    a.join(", ", last: " and ", default: "")
  } else {
    [#a.first(default: "") et al.]
  }
}

// Title page function (your snippet, packaged)
#let titlepage(
  title: auto,
  author: auto,
  term: [Fall 2026],
  logo: auto,
  paper: "presentation-16-9",
  margin: (left: 1.25em, right: 1.25em, top: 2.25em, bottom: 1.5em),
) = context {
  // Set default slide geometry for the whole deck from here onward.
  set page(paper: paper, margin: margin)

  // Render the title page with header/footer suppressed.
  let t = document.title
  let a = author-name(author: author)

  page(paper: paper, margin: margin, header: none, footer: none)[
    #align(horizon + center, text(size: 32pt, weight: "semibold")[#t])
    #align(horizon + center, text(size: 24pt)[#a])
    #align(horizon + center, [#logo])
    #align(horizon + center, text(size: 18pt)[#term])
  ]

  // Move to the next slide (weak avoids accidental blank pages).
  pagebreak(weak: true)
}

#let outlinepage(
  title: [Outline],
  depth: 2,
  target: heading, // what to outline; default is headings
) = [
  #page(header: none, footer: none)[
    #outline(target: target, depth: depth)
  ]
]
