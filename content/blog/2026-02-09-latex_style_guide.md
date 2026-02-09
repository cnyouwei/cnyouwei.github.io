---
title: LaTeX Style Guide for Operations Research
date: 2026-02-09
summary: A LaTeX style guide tailored to Operations Research papers.
tags: [latex, notes, operations research]
---

This is a LaTeX style guide tailored to Operations Research papers. It includes:

- A **plain `article` template** you can use for drafts and preprints.
- A **package set** and ordering rules that work well for OR.
- **Notation + macro discipline** (models, constraints, index sets, dual variables).
- **Math typography** and **font styles** (e.g., boldface vectors/matrices) in OR practice.
- “Easy to ignore” **English and typographic micro‑rules**: punctuation, dashes, capitalization, spacing, etc.

> Venue note: if a journal/conference provides a `.cls`/author kit, **use it**. Keep the notation/macros from this guide; swap the class.

---

## Plain OR paper template

Paste into `main.tex`. It is a clean base for OR drafts, with OR-friendly theorem + algorithm support.

```latex
\documentclass[11pt]{article}

% --------------------
% Language
% --------------------
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage[english]{babel}

% --------------------
% Layout + typography
% --------------------
\usepackage[margin=1in]{geometry}
\usepackage{microtype}
\usepackage{csquotes}
\usepackage{xcolor}

% --------------------
% Math
% --------------------
\usepackage{amsmath, amssymb, amsthm}
\usepackage{mathtools}
\usepackage{bm}
\usepackage{siunitx}

% --------------------
% Algorithms (choose ONE stack)
% --------------------
\usepackage{algorithm}
\usepackage{algpseudocode}
% Alternative (not compatible with algorithmicx syntax):
% \usepackage[ruled,vlined]{algorithm2e}

% --------------------
% Figures and tables
% --------------------
\usepackage{graphicx}
\usepackage{subcaption}
\usepackage{booktabs}

% --------------------
% Lists
% --------------------
\usepackage{enumitem}
\setlist[itemize]{topsep=4pt,itemsep=2pt}
\setlist[enumerate]{topsep=4pt,itemsep=2pt}

% --------------------
% Hyperlinks: load late
% --------------------
\usepackage[colorlinks=true,allcolors=blue]{hyperref}
\usepackage[nameinlink,noabbrev]{cleveref}

% --------------------
% Bibliography (draft-friendly)
% --------------------
\usepackage[
  backend=biber,
  style=authoryear,   % common in OR journals
  sorting=nyt,
  giveninits=true,
  maxbibnames=99,
  doi=true,
  url=true,
  isbn=false
]{biblatex}
\addbibresource{references.bib}

% --------------------
% OR theorem environments
% --------------------
\theoremstyle{plain}
\newtheorem{theorem}{Theorem}
\newtheorem{lemma}{Lemma}
\newtheorem{proposition}{Proposition}
\newtheorem{corollary}{Corollary}

\theoremstyle{definition}
\newtheorem{definition}{Definition}
\newtheorem{assumption}{Assumption}

\theoremstyle{remark}
\newtheorem{remark}{Remark}

% --------------------
% Your notation
% --------------------
\input{macros.tex}

\title{Your OR Paper Title}
\author{First Author \and Second Author}
\date{} % often left empty in submissions

\begin{document}
\maketitle

\begin{abstract}
State the problem, your contribution (model/algorithm/insight), and the key results (theoretical + computational).
\end{abstract}

\section{Introduction}
Introduce the decision problem and motivate relevance. Summarize contributions crisply.

\section{Model}
An example model appears in \cref{prob:base}.

\begin{subequations}\label{prob:base}
\begin{align}
\min_{\vect{x}} \quad & \vect{c}^{\mathsf{T}}\vect{x} \label{prob:base:obj}\\
\st \quad
& \mat{A}\vect{x} \ge \vect{b}, \label{prob:base:constr1}\\
& \vect{x} \in \Reals_+^n. \label{prob:base:dom}
\end{align}
\end{subequations}

\section{Algorithm}
\begin{algorithm}[t]
\caption{Generic decomposition framework}
\label{alg:decomp}
\begin{algorithmic}[1]
\State Initialize master problem.
\While{termination criterion not met}
  \State Solve master problem; obtain candidate solution.
  \State Solve subproblem; generate cut if needed.
\EndWhile
\State \Return best feasible solution found.
\end{algorithmic}
\end{algorithm}

\section{Theory}
\begin{theorem}\label{thm:convergence}
Under \cref{ass:regularity}, Algorithm~\ref{alg:decomp} terminates in finitely many iterations.
\end{theorem}

\begin{proof}
Sketch the proof structure; avoid long narrative if a standard argument applies.
\end{proof}

\section{Computational experiments}
Describe instances, parameter settings, hardware, solver versions, and evaluation protocol.

\printbibliography

\end{document}
```

---

## Packages: OR baseline and options

### Baseline (recommended for most OR drafts)

- **Math and structure**
  - `amsmath, amssymb, amsthm`: models, proofs, theorem environments.
  - `mathtools`: improves `amsmath` (paired delimiters, etc.).
  - `bm`: reliable bold math (Greek, symbols).
  - `siunitx`: units/numbers (important for computational tables, time units).
- **Algorithms**
  - `algorithm` + `algpseudocode` (algorithmicx): flexible pseudocode.
  - *(Alternative)* `algorithm2e`: produces good-looking algorithms but has its own syntax.
  - Pick **one** to avoid conflicts.
- **Figures/tables**
  - `graphicx`, `subcaption`, `booktabs`.
- **Refs**
  - `hyperref` (late), then `cleveref` for “Eq./Alg./Thm.” automation.
- **Bibliography**
  - `biblatex` + `biber` in drafts; switch to venue style later if needed.

### OR-useful optional packages

- **Optimization formulation helpers**
  - `optidef`: nice “minimize / subject to” blocks (convenient, but check compatibility with venue).
  - If you keep the formulation in plain `align`, you’ll never be blocked by venue constraints.
- **Diagrams**
  - `tikz` / `pgfplots`: great for network flow diagrams or stylized plots, but can slow compilation.
  - Often best practice is: generate plots with Python/R/Matlab → include as PDF.
- **Tables**
  - `threeparttable` (notes under tables).
  - `tabularx` (automatic width).
  - `multirow`, `makecell` for complex headers (use sparingly).

### Package ordering rules

- Fonts early, then math, then floats/tables, then `hyperref`, then `cleveref`.
- `\input{macros.tex}` after packages.
- Avoid “mega-packages” that change defaults globally unless you must.

---

## Notation and macro policy for OR

OR papers often fail on one of two extremes:
- **No macros** → inconsistent notation and formatting drift.
- **Too many macros** → unreadable source and brittle compilation.

Aim for a small, semantic macro set.

### Typical OR notation categories

A common, readable split:

- **Sets**: calligraphic, e.g., $\mathcal{I}, \mathcal{J}, \mathcal{A}$  
- **Indices**: roman letters, e.g., $i \in \mathcal{I}$, $j \in \mathcal{J}$
- **Decision variables**: italic scalars ($x_{ij}$), bold vectors/matrices ($\bm{x}$, $\bm{A}$)
- **Parameters**: italic ($c_{ij}$), sometimes roman for fixed constants (taste/venue)
- **Dual variables / multipliers**: Greek letters (e.g., $\pi, \lambda$)
- **Random variables**: uppercase ($D$) or decorated (e.g., $\tilde{D}$); choose one convention

### Macro naming conventions (pragmatic)

- `\setI`, `\setJ` for index sets (or `\mathcal{I}` inline if not repeated often).
- `\vect{}` and `\mat{}` for vectors/matrices.
- Operators: `\argmin`, `\argmax`, `\st`, `\E`, `\Prob`.
- Indicator function: `\ind{...}` or `\1{...}`.

**Do not** redefine core symbols (`\le`, `\epsilon`, etc.) unless a strong reason exists.

### Label namespaces

Suggested label prefixes:

- `sec:...` — section
- `prob:...` — models/problems
- `eq:...` — single equations
- `fig:...` — figures
- `alg:...` — algorithms
- `thm:...`, `lem:...`, `prop:...`, `ass:...`

Example:
- `\label{prob:facility}` for a facility location model
- `\label{prob:facility:cap}` for its capacity constraint

---

## Optimization model formatting

### Preferred structure: `subequations` + `align`

This gives you:
- A single “model number” (e.g., (1))
- Constraint letters (e.g., (1a), (1b), …)
- Individual constraint labels for precise referencing

Example: MILP model.

```latex
\begin{subequations}\label{prob:ufl}
\begin{align}
\min_{x,y} \quad
& \sum_{i\in\setI}\sum_{j\in\setJ} c_{ij} x_{ij} + \sum_{j\in\setJ} f_j y_j \label{prob:ufl:obj}\\
\st \quad
& \sum_{j\in\setJ} x_{ij} = 1, && \forall i\in\setI, \label{prob:ufl:assign}\\
& x_{ij} \le y_j, && \forall i\in\setI,\, \forall j\in\setJ, \label{prob:ufl:open}\\
& x_{ij} \ge 0, && \forall i\in\setI,\, \forall j\in\setJ, \label{prob:ufl:xdom}\\
& y_j \in \{0,1\}, && \forall j\in\setJ. \label{prob:ufl:ydom}
\end{align}
\end{subequations}
```

Then reference:
- “Model \cref{prob:ufl}”
- “Constraint \cref{prob:ufl:open}”
- “Constraints \cref{prob:ufl:assign,prob:ufl:open}”

### “s.t.” and quantifiers

- Write **s.t.** as text: `\st` macro (upright roman), not italic math letters.
- In OR, quantifiers are often best as side conditions:
  - `&& \forall i\in\setI` is clear and compact.
- Avoid writing constraints with heavy logic symbols (`\forall`, `\exists`) inline unless needed.

### Punctuation

Treat the whole optimization block as part of a sentence. A common convention:
- Put **no period** after the last constraint if followed by text immediately, or
- Put a **period** after the final line if it ends the sentence.

Be consistent.

### Naming models: (LP), (MIP), (SP), …

If you want named models like “(MIP)”, use `\tag{MIP}`:

```latex
\begin{align}
\min_x \quad & c^\top x \\
\st \quad & Ax \ge b, \tag{MIP}\label{prob:mip}
\end{align}
```

Note: `\tag` is manual; use it sparingly and only if your venue supports it.

### Dual variables and Lagrangian notation

Best practice in OR manuscripts:
- Use **explicit dual variable names** with constraints (when deriving duals/KKT).
- Keep a consistent mapping:
  - primal constraints → dual multipliers (e.g., $\pi_i$)
  - variable bounds → multipliers (e.g., $\mu_j \ge 0$)

If you annotate constraints with duals, do it cleanly:

```latex
& \sum_{j\in\setJ} x_{ij} = 1, && \forall i\in\setI, \quad (\pi_i) \\
```

Be careful: annotation is helpful in derivations, but can clutter final models.

---

## Algorithms and pseudocode

OR papers often include decomposition, heuristics, DP, or metaheuristics. Keep algorithms **precise and easy to cross-reference**.

### Use structured pseudocode with line numbers

With `algpseudocode`:

```latex
\begin{algorithm}[t]
\caption{Benders decomposition (high-level)}
\label{alg:benders}
\begin{algorithmic}[1]
\State Initialize master problem with no Benders cuts.
\Repeat
  \State Solve master; obtain $(\hat{y}, \hat{\theta})$.
  \State Solve subproblem at $\hat{y}$.
  \If{subproblem infeasible}
    \State Add feasibility cut.
  \Else
    \State Add optimality cut and update incumbent.
  \EndIf
\Until{no violated cuts remain}
\end{algorithmic}
\end{algorithm}
```

Refer to `Algorithm~\ref{alg:benders}` (or `\cref{alg:benders}`).

### Algorithm typography rules

- Algorithm captions should describe the method, not “Algorithm 1”.
- Use consistent naming: “Procedure”, “Heuristic”, “Framework”, “Algorithm”.
- Define termination criteria precisely (gap, iterations, time limit).

### Complexity statements

Write complexity as math:
- $\mathcal{O}(n\log n)$, not “O(n log n)” in text mode.

Define an operator macro if you use it often:
```latex
\newcommand{\bigO}{\mathcal{O}}
```

---

## Theorems, propositions, lemmas, and proofs

OR papers frequently mix theory and computation. Theorem environments should look professional and be easy to reference.

### Use `amsthm` styles intentionally

- `plain` (italic body): theorem/lemma/proposition/corollary.
- `definition` (upright body): definitions/assumptions.
- `remark` (upright body): remarks.

### Label theorems and assumptions

```latex
\begin{assumption}\label{ass:convex}
The feasible region is nonempty and compact.
\end{assumption}
```

Then: `Under \cref{ass:convex}, …`

### Proof hygiene

- Use `\begin{proof}...\end{proof}`.
- If you end with a displayed equation, use `\qedhere` to position the □ nicely.

```latex
\begin{proof}
...
\begin{equation}
  x^\star \in \argmin_{x\in X} f(x). \qedhere
\end{equation}
\end{proof}
```

Use clear structure:
1. State what you prove.
2. Give the main inequality or argument.
3. Close cleanly.

---

## Math typography and font styles in OR

This section is about **meaning encoded in fonts**—a major readability factor in OR.

### Recommended OR typography conventions

While there’s variation by subfield, a robust and readable default is:

- Scalars: italic ($x$, $c_{ij}$)
- Vectors: **bold italic** ($\bm{x}$, $\bm{c}$)
- Matrices: **bold italic** ($\bm{A}$) or bold uppercase (field preference)
- Sets: calligraphic ($\mathcal{I}$)
- Functions/operators: upright (`\min`, `\argmin`, `\log`)
- Constants: upright when they are true constants ($\mathrm{e}$, $\mathrm{i}$)

### Implementing bold vectors/matrices

Use `bm` and define macros:

```latex
\newcommand{\vect}[1]{\bm{#1}}
\newcommand{\mat}[1]{\bm{#1}}
```

Why `bm`?
- It correctly bolds **Greek** and symbols (`\vect{\lambda}`), where `\mathbf` fails.

### Avoiding typography ambiguity in OR notation

OR manuscripts often overload symbols:
- $c$ as cost *and* speed of light (rare, but the idea stands)
- $T$ as time horizon and transpose
- $\lambda$ as Lagrange multiplier and arrival rate (queueing)

Best practice:
- Use `\top` for transpose (as a superscript), e.g., $\bm{c}^\top \bm{x}$.
- If your subfield uses $\lambda$ heavily (queueing + duality), consider different Greek letters or explicit subscripts.

### Calligraphic, blackboard, fraktur

Use font families as **semantic classes**, not decoration:

- $\mathcal{I}$ sets / index families
- $\mathbb{R}$ number systems
- $\mathfrak{g}$ (rare in OR; more common in algebra)

---

## Probability, expectations, and stochastic models

Many OR papers involve stochastic programming, MDPs, queueing, or robust optimization. Notation consistency is critical.

### Expectation and probability operators

Define:
```latex
\newcommand{\Prob}{\mathbb{P}}
\newcommand{\E}{\mathbb{E}}
```

Conditional expectation should use `\mid` (proper spacing), not `|`:

```latex
\E[X \mid Y=y]
\Prob(A \mid B)
```

If you use conditioning often, define a `\given` macro:

```latex
\newcommand{\given}{\,\middle|\,}
```

Then: `\E[X \given Y]`.

### Random variables vs realizations

Pick one convention and state it:

- **Convention A (common):** random variables uppercase ($D$), realizations lowercase ($d$).
- **Convention B:** random variables decorated ($\tilde{D}$), decisions plain.

Avoid mixing conventions across sections.

---

## Computational experiments reporting

This is OR-specific and often decisive in reviews.

### Report what reviewers will look for

- Instance generation / source (public set, synthetic process, etc.)
- Number of instances, size parameters
- Hardware (CPU model, RAM), OS
- Solver and version (e.g., Gurobi, CPLEX), parameter settings
- Time limits, optimality gaps, random seeds
- Baselines and fairness (same machine, same termination rules)

### Tables: align and compress without losing truth

Use `booktabs` + `siunitx` alignment.

Include:
- mean ± std (if randomized)
- median + IQR (often robust)
- best-known objective, gap, time

Avoid “too many decimals”:
- pick meaningful precision (e.g., time to 0.01s may be nonsense if system noise is larger).

---

## Figures and tables

(Short version: same best practices as general scientific LaTeX, with OR emphasis on clarity and comparability.)

### Figures in OR papers

- Prefer **vector PDF** for plots.
- Label axes with units (use `siunitx` in plot labels if possible).
- If you compare methods, keep line styles distinct and legends readable.

### Tables in OR papers

- Avoid vertical lines; use whitespace and `booktabs`.
- Align numbers by decimal point (`S` columns).
- Always specify what “gap” means (relative? absolute? vs best-known?).

---

## Cross-references and hyperlinks

OR manuscripts benefit disproportionately from good cross-referencing.

- Use `\cref{...}` for:
  - Models `\cref{prob:ufl}`
  - Constraints `\cref{prob:ufl:open}`
  - Algorithms `\cref{alg:benders}`
  - Theorems `\cref{thm:convergence}`
  - Assumptions `\cref{ass:convex}`

Nonbreaking spaces still matter if you ever use manual references:
- `Algorithm~\ref{alg:...}`, `Theorem~\ref{thm:...}`

---

## Bibliography and citations

### Style choice in OR

- Many OR journals use **author–year** citations; some use numeric.
- The safest draft choice is `biblatex` with `style=authoryear`.
- Switch to venue-required style at submission time.

### Capitalization in titles

Protect acronyms and proper nouns in `.bib`:

```bibtex
title = {A {Benders} decomposition approach for {MILP} models},
```

### Citation commands

With `biblatex`:
- `\parencite{key}` → (Author, Year)
- `\textcite{key}` → Author (Year)

Use `\textcite` when the author name is grammatically part of the sentence.

---

## English + typographic micro-rules for OR writing

These are the small things that make OR manuscripts feel “review-ready.”

### Hyphenation in OR terms

Use hyphens consistently:

- “mixed-integer linear program” (MILP)
- “two-stage stochastic program”
- “polynomial-time algorithm”
- “cut-generating function” (if used adjectivally)

### Dashes (hyphen/en dash/em dash)

- Hyphen `-`: compound modifiers (“branch-and-cut”).
- En dash `--`: ranges (“10--20”) and connections (“Dantzig--Wolfe”).
- Em dash `---`: parenthetical breaks—use sparingly in formal OR writing.

### Common OR abbreviations and capitalization

- NP-hard (hyphenated, “NP” uppercase)
- MIP/MILP/LP/QP/SDP (uppercase; define once)
- KKT (uppercase)
- “Benders decomposition,” “Dantzig–Wolfe decomposition” (proper nouns)

### “i.e.” and “e.g.”

- “e.g.,” and “i.e.,” often take a comma in US style: “e.g., we consider…”.
- Avoid stuffing long lists after “e.g.,”; use “for example” if the sentence gets heavy.

### Optimization language: avoid ambiguity

Be explicit about what is being optimized and over what domain.

Prefer:
- “We solve the MILP in \cref{prob:ufl}.”
- “We minimize expected cost over first-stage decisions.”

Avoid:
- “We optimize the model.” (What objective? what constraints? what algorithm?)

### Equations are sentences

This is especially important in model-heavy OR writing.
- Put commas and periods in displayed math when grammatically needed.
- Don’t leave the reader guessing whether constraints are complete.

---

## OR-specific checklist

**Model and notation**
- [ ] Sets/indices/parameters/variables are defined once, early (often in a “Notation” subsection).
- [ ] Vectors/matrices use consistent typography (`\vect{}`, `\mat{}`).
- [ ] Every model has a global label (`prob:...`) and key constraints have labels.
- [ ] “s.t.” and quantifiers are formatted consistently.

**Theory**
- [ ] Assumptions are explicitly stated and labeled.
- [ ] Theorems/lemmas are labeled and referenced with `\cref`.
- [ ] Proofs end cleanly, with `\qedhere` if needed.

**Algorithms**
- [ ] Pseudocode has line numbers.
- [ ] Termination criteria and complexity statements are explicit.

**Computation**
- [ ] Instances, hardware, solver versions, and time limits are reported.
- [ ] Metrics (gap, time, objective) are defined unambiguously.
- [ ] Tables align decimals and avoid excessive precision.

---

## Appendix: starter `macros.tex` for OR

Paste into `macros.tex` and tailor.

```latex
% macros.tex — Operations Research notation

% --- Number systems ---
\newcommand{\Reals}{\mathbb{R}}
\newcommand{\Integers}{\mathbb{Z}}
\newcommand{\Realspos}{\Reals_{+}}
\newcommand{\Integerspos}{\Integers_{+}}

% --- Sets (use calligraphic for index sets) ---
\newcommand{\setI}{\mathcal{I}}
\newcommand{\setJ}{\mathcal{J}}
\newcommand{\setK}{\mathcal{K}}
\newcommand{\setA}{\mathcal{A}}
\newcommand{\setN}{\mathcal{N}}
\newcommand{\setU}{\mathcal{U}}
\newcommand{\setO}{\Omega} % scenario set often denoted Omega

% --- Linear algebra objects ---
\newcommand{\vect}[1]{\bm{#1}} % bold italic vector
\newcommand{\mat}[1]{\bm{#1}}  % bold italic matrix

% --- Transpose and inner products ---
\newcommand{\T}{^{\mathsf{T}}}
\newcommand{\ip}[2]{\left\langle #1, #2 \right\rangle}

% --- Optimization operators ---
\DeclareMathOperator*{\argmin}{arg\,min}
\DeclareMathOperator*{\argmax}{arg\,max}

% Subject-to (upright text) and "min/max" in model blocks
\newcommand{\st}{\text{s.t.}}

% --- Probability and expectation ---
\newcommand{\Prob}{\mathbb{P}}
\newcommand{\E}{\mathbb{E}}
\newcommand{\Var}{\operatorname{Var}}

% Conditioning bar with good spacing
\newcommand{\given}{\,\middle|\,}

% --- Differential (if needed) ---
\newcommand{\diff}{\mathop{}\!\mathrm{d}}

% --- Complexity ---
\newcommand{\bigO}{\mathcal{O}}

% --- Norms / abs / floor / ceil ---
\DeclarePairedDelimiter{\abs}{\lvert}{\rvert}
\DeclarePairedDelimiter{\norm}{\lVert}{\rVert}
\DeclarePairedDelimiter{\ceil}{\lceil}{\rceil}
\DeclarePairedDelimiter{\floor}{\lfloor}{\rfloor}

% Usage:
% \abs{x}, \abs*{x} for auto sizing
% \norm{x}, \ceil*{x}, etc.

% --- Indicator function (choose one approach) ---
% Option 1: bold 1 (portable)
\newcommand{\ind}{\mathbf{1}}
% Then write: \ind\{A\} or define a wrapper:
\newcommand{\Ind}[1]{\ind\{#1\}}

% If you prefer a blackboard 1, consider:
% \usepackage{bbm}
% \newcommand{\ind}{\mathbbm{1}}

% --- Common constants (upright) ---
\newcommand{\e}{\mathrm{e}}
\newcommand{\ii}{\mathrm{i}}
```

---

## Practical next steps

To align with a specific OR venue:
- Replace `\documentclass{article}` with the venue class.
- Adjust bibliography style to the required one (some venues require BibTeX styles).
- Keep your **notation macros** stable; this is what preserves clarity across formats.
