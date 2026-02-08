#import "@preview/cetz:0.4.2"
#import "@preview/fletcher:0.5.8" as fletcher: diagram, edge, node
#import fletcher.shapes: brace, pill

// Helper node for course boxes in curriculum map
#let course(pos, code, title, tint: blue, name: none) = node(
  pos,
  name: name,
  shape: rect,
  width: 70mm,
  inset: 10pt,
  corner-radius: 14pt,
  fill: tint.lighten(70%),
  stroke: 2pt + tint.darken(10%),
  align(center)[
    #text(size: 0.85em)[*#code*] \
    #text(size: 0.7em)[#title]
  ],
)

// Curriculum map diagram
#let curriculum_map() = {
  diagram(
    spacing: 50pt,
    cell-size: (66mm, 24mm),
    edge-stroke: 1.25pt,
    edge-corner-radius: 5pt,
    mark-scale: 80%,

    // ----------------------------
    // Center course
    // ----------------------------
    course((1, 1), [IEDA3250], [Stochastic Models], tint: red.darken(20%), name: <SM>),

    // ----------------------------
    // Foundation (top-left cluster)
    // ----------------------------
    course((0, 0), [IEDA2520], [Probability for Engineers], tint: olive.transparentize(50%), name: <P>),
    course((0, 1), [IEDA2540], [Statistics for Engineers], tint: olive.transparentize(50%), name: <S>),
    course((1, 0), [IEDA3010], [Prescriptive Analytics], tint: orange.transparentize(60%), name: <PA>),

    // ----------------------------
    // Follow-ups surrounding SM
    // (top / right / bottom-right / bottom)
    // ----------------------------
    course((0, 2), [IEDA4180], [Service Engineering], tint: blue.transparentize(60%), name: <SE>),
    course((1, 2), [IEDA4510], [Systems Risk Management], tint: blue.transparentize(60%), name: <RM>),
    course((2, 2), [IEDA4420], [Dynamic Pricing and \ Revenue Management], tint: blue.transparentize(60%), name: <PR>),

    course(
      (2, 0),
      [IEDA4331],
      [Quantitative Methods in Financial Engineering],
      tint: blue.transparentize(60%),
      name: <QF1>,
    ),
    course(
      (2, 1),
      [IEDA4520],
      [Numerical Methods for Financial Engineering],
      tint: blue.transparentize(60%),
      name: <QF2>,
    ),

    // ----------------------------
    // Prerequisite edges (solid)
    // ----------------------------
    edge(<P>, <S>, marks: "->"),
    edge(<P>, <SM>, marks: "->"),
    edge(<S>, <SM>, marks: "->"),

    // Prescriptive Analytics as conceptual bridge (dashed)
    edge(
      <PA>,
      <SM>,
      marks: "->",
      dash: "dashed",
      label: text(size: 0.7em)[stochastic \ extension],
      label-sep: 0.4em,
      label-angle: 90deg,
      // bend: 12deg,
    ),

    // ----------------------------
    // Stochastic Models -> follow-ups
    // ----------------------------
    edge(<SM>, <SE>, marks: "->"),
    edge(<SM>, <RM>, marks: "->"),
    edge(<SM>, <PR>, marks: "->"),
    edge(<SM>, <QF1>, marks: "->"),
    edge(<QF1>, <QF2>, marks: "->"),
    edge(<SM>, <QF2>, marks: "->"),


    edge(<PA>, <RM>, marks: "->", bend: -55deg),
    edge(<PA>, <PR>, marks: "->"),

    node(
      [], // no content; just draw a box around the enclosed nodes
      enclose: (<P>, <S>, <PA>, <SM>),
      name: <FOUND>,
      shape: rect,
      inset: 20pt, // scalar (important)
      corner-radius: 32pt,
      fill: rgb("EAF2F5"),
      stroke: 1.5pt + rgb("#003366"),
      snap: false, // keep edges snapping to actual course nodes
    ),
    node(
      <FOUND.north>,
      rect(
        fill: white,
        stroke: 1.5pt + rgb("#003366"),
        radius: 10pt,
        inset: 8pt,
        text(size: 0.7em, weight: "bold", fill: rgb("#003366"))[
          Foundational courses
        ],
      ),
      snap: false,
    ),
  )
}

// Inspection paradox illustration plot
#let inspection-paradox-plot() = {
  // 1 coordinate unit = 0.33cm (tune for your slide sizing)
  cetz.canvas(length: 0.33cm, {
    import cetz.draw: *

    // ----------------------------
    // Icon "stamps" (replace with SVG if you prefer)
    // ----------------------------
    let bus = text(size: 1.2em)[🚌]
    let person = text(size: 0.8em)[🧍]

    // Global styling defaults
    set-style(
      stroke: 1pt + luma(25%),
      fill: none,
      content: (padding: 0.12),
      line: (stroke: 1pt + luma(25%)),
    )

    let ticks = (0, 10, 20, 30, 40)

    // Draw one row (a "timeline" at vertical coordinate y)
    let row(y, title, buses, arrive_t, next_t, w_label) = {
      // Background strip
      rect((0, y + 0.55), (20, y - 0.55), fill: luma(97%), stroke: none)

      // Axis with arrow
      line((0, y), (20.8, y), mark: (end: ">"), stroke: luma(30%))

      // Ticks + labels
      for t in ticks {
        line((t, y + 0.12), (t, y - 0.12), stroke: luma(35%))
        content((t, y - 0.28), text(size: 0.75em)[#t], anchor: "north")
      }

      // Row title (left)
      content((20, y - 4), text(size: 0.75em)[#title], anchor: "center")

      // Headway shading + headway-length labels
      for i in range(0, buses.len() - 1) {
        let a = buses.at(i)
        let b = buses.at(i + 1)
        let gap = b - a

        // Shade longer gaps slightly darker (to cue "size bias")
        rect(
          (a, y + 0.45),
          (b, y - 0.45),
          fill: if gap > 20 { luma(80%) } else { luma(95%) },
          stroke: none,
        )
        content(((a + b) / 2, y - 3), text(size: 0.72em)[#gap min], anchor: "south")
      }

      // Bus icons at arrival epochs
      for i in range(0, buses.len()) {
        let t = buses.at(i)
        // small tick
        line((t, y + 0.20), (t, y - 0.20), stroke: luma(20%))
        // bus icon
        content((t, y + 0.08), bus, anchor: "south")
      }

      // Passenger arrival (random inspection time)
      content((arrive_t, y + 0.4), person, anchor: "south")
      // line((arrive_t, y + 0.78), (arrive_t, y + 0.10), stroke: luma(35%), mark: (end: ">"))

      // Waiting time arrow/bracket to the next bus
      line(
        (arrive_t + 1, y + 2),
        (next_t - 2, y + 2),
        stroke: (paint: luma(25%), dash: "dashed"),
        mark: (start: "<", end: ">"),
      )
      content(((arrive_t + next_t) / 2, y + 2.75), text(size: 0.6em)[#w_label], anchor: "south")
    }

    row(
      14,
      [Deterministic schedule],
      (0, 20, 40),
      11,
      20,
      [wait $W=9$ min],
    )
    row(
      3,
      [Variable schedule — same mean 20],
      (0, 8, 40),
      11,
      40,
      [wait $W=29$ min],
    )
  })
}

// Random-walk transition diagram

#let state(pos, label: none, tint: navy.lighten(90%), name: none) = node(
  pos,
  name: name,
  shape: circle,
  width: 12mm,
  inset: 0pt,
  fill: tint,
  stroke: 1.5pt + navy.lighten(30%),
  align(center)[
    #text(size: 1em)[#label]
  ],
)

#let random-walk-transition-diagram() = {
  diagram(
    spacing: 20pt,

    node((-4, 0), shape: circle, name: <left-ellipsis>)[
      #text(size: 1em)[$dots.c$]
    ],
    state((-3, 0), label: "-3", name: <Sneg3>),
    state((-2, 0), label: "-2", name: <Sneg2>),
    state((-1, 0), label: "-1", name: <Sneg1>),
    state((0, 0), label: "0", name: <S0>),
    state((1, 0), label: "1", name: <S1>),
    state((2, 0), label: "2", name: <S2>),
    state((3, 0), label: "3", name: <S3>),
    node((4, 0), shape: circle, name: <right-ellipsis>)[
      #text(size: 1em)[$dots.c$]
    ],

    edge(<left-ellipsis>, <Sneg3>, marks: "->", bend: 60deg, label: text(size: 0.7em)[$p$], label-sep: 0em),
    edge(<Sneg3>, <left-ellipsis>, marks: "->", bend: 60deg, label: text(size: 0.7em)[$q$], label-sep: 0em),
    edge(<Sneg3>, <Sneg2>, marks: "->", bend: 60deg, label: text(size: 0.7em)[$p$], label-sep: 0em),
    edge(<Sneg2>, <Sneg3>, marks: "->", bend: 60deg, label: text(size: 0.7em)[$q$], label-sep: 0em),
    edge(<Sneg2>, <Sneg1>, marks: "->", bend: 60deg, label: text(size: 0.7em)[$p$], label-sep: 0em),
    edge(<Sneg1>, <Sneg2>, marks: "->", bend: 60deg, label: text(size: 0.7em)[$q$], label-sep: 0em),
    edge(<Sneg1>, <S0>, marks: "->", bend: 60deg, label: text(size: 0.7em)[$p$], label-sep: 0em),
    edge(<S0>, <Sneg1>, marks: "->", bend: 60deg, label: text(size: 0.7em)[$q$], label-sep: 0em),
    edge(<S0>, <S1>, marks: "->", bend: 60deg, label: text(size: 0.7em)[$p$], label-sep: 0em),
    edge(<S1>, <S0>, marks: "->", bend: 60deg, label: text(size: 0.7em)[$q$], label-sep: 0em),
    edge(<S1>, <S2>, marks: "->", bend: 60deg, label: text(size: 0.7em)[$p$], label-sep: 0em),
    edge(<S2>, <S1>, marks: "->", bend: 60deg, label: text(size: 0.7em)[$q$], label-sep: 0em),
    edge(<S2>, <S3>, marks: "->", bend: 60deg, label: text(size: 0.7em)[$p$], label-sep: 0em),
    edge(<S3>, <S2>, marks: "->", bend: 60deg, label: text(size: 0.7em)[$q$], label-sep: 0em),
    edge(<S3>, <right-ellipsis>, marks: "->", bend: 60deg, label: text(size: 0.7em)[$p$], label-sep: 0em),
    edge(<right-ellipsis>, <S3>, marks: "->", bend: 60deg, label: text(size: 0.7em)[$q$], label-sep: 0em),
  )
}

// 2D simple random walk (local transition diagram around (0,0))

#let random-walk-2d-transition-diagram() = {
  diagram(
    spacing: 50pt,

    // node((-4, 0), shape: circle, name: <left-ellipsis>)[
    //   #text(size: 1em)[$dots.c$]
    // ],

    state((0, 0), name: <00>),
    state((1, 0), name: <01>),
    state((2, 0), name: <02>),
    state((0, 1.4), name: <10>),
    state((1, 1.4), name: <11>),
    state((2, 1.4), name: <12>),
    state((0, 2.8), name: <20>),
    state((1, 2.8), name: <21>),
    state((2, 2.8), name: <22>),
    // node((4, 0), shape: circle, name: <right-ellipsis>)[
    //   // #text(size: 1em)[$dots.c$]
    // ],

    edge(
      <00>,
      <01>,
      marks: "->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <01>,
      <00>,
      marks: "->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <00>,
      <10>,
      marks: "->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <10>,
      <00>,
      marks: "->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <01>,
      <11>,
      marks: "->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <11>,
      <01>,
      marks: "->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <10>,
      <11>,
      marks: "->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <11>,
      <10>,
      marks: "->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <11>,
      <21>,
      marks: "->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <21>,
      <11>,
      marks: "->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <12>,
      <22>,
      marks: "->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <22>,
      <12>,
      marks: "->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <21>,
      <22>,
      marks: "->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <22>,
      <21>,
      marks: "->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <01>,
      <02>,
      marks: "->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <02>,
      <01>,
      marks: "->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <02>,
      <12>,
      marks: "->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <12>,
      <02>,
      marks: "->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <11>,
      <12>,
      marks: "->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <12>,
      <11>,
      marks: "->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <10>,
      <20>,
      marks: "->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <20>,
      <10>,
      marks: "->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <20>,
      <21>,
      marks: "->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <21>,
      <20>,
      marks: "->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <00>,
      (-1, 0),
      marks: "-->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <00>,
      (0, -1),
      marks: "-->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <01>,
      (1, -1),
      marks: "-->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <02>,
      (2, -1),
      marks: "-->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <02>,
      (3, 0),
      marks: "-->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <12>,
      (3, 1.4),
      marks: "-->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <22>,
      (3, 2.8),
      marks: "-->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <22>,
      (2, 4),
      marks: "-->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <21>,
      (1, 4),
      marks: "-->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <20>,
      (0, 4),
      marks: "-->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <20>,
      (-1, 2.8),
      marks: "-->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
    edge(
      <10>,
      (-1, 1.4),
      marks: "-->",
      bend: 32deg,
      label: text(size: 0.5em)[$frac(1, 4, style: "horizontal")$],
      label-sep: 0em,
    ),
  )
}

// Machine up/down DTMC transition diagram
#let machine-up-down-transition-diagram() = {
  diagram(
    spacing: 20pt,

    state((0, 0), label: $U$, name: <U>, tint: green.lighten(85%)),
    state((2.5, 0), label: $D$, name: <D>, tint: red.lighten(85%)),

    edge(
      <U>,
      <D>,
      marks: "->",
      bend: 45deg,
      label: text(size: 0.7em)[$alpha$],
      label-sep: 0em,
    ),
    edge(
      <D>,
      <U>,
      marks: "->",
      bend: 45deg,
      label: text(size: 0.7em)[$beta$],
      label-sep: 0em,
    ),

    edge(
      <U>,
      <U>,
      marks: "->",
      bend: 145deg,
      loop-angle: 180deg,
      label: text(size: 0.7em)[$1 - alpha$],
      label-pos: 0.5,
      label-sep: 0em,
    ),
    edge(
      <D>,
      <D>,
      marks: "->",
      bend: 145deg,
      loop-angle: 0deg,
      label: text(size: 0.7em)[$1 - beta$],
      label-pos: 0.5,
      label-sep: 0em,
    ),
  )
}

// next-day depends on the last 3 days
#let machine-maintenance-augmented-state-diagram() = {
  diagram(
    spacing: 20pt,

    state((0, 0), label: $D$, name: <D>, tint: red.lighten(30%)),
    state((2.5, 0), label: $U_0$, name: <U0>, tint: olive.lighten(30%)),
    state((5, 0), label: $U_1$, name: <U1>, tint: olive.lighten(50%)),
    state((7.5, 0), label: $U_2$, name: <U2>, tint: olive.lighten(70%)),
    state((10, 0), label: $U_(3+)$, name: <U3>, tint: olive.lighten(90%)),


    // staying Up increments the "age since maintenance"
    edge(<U0>, <U1>, marks: "->", label: text(size: 0.65em)[$1-alpha_0$], label-sep: 0.1em),
    edge(<U1>, <U2>, marks: "->", label: text(size: 0.65em)[$1-alpha_1$], label-sep: 0.1em),
    edge(<U2>, <U3>, marks: "->", label: text(size: 0.65em)[$1-alpha_2$], label-sep: 0.1em),

    // once in 3+ bucket, it stays in 3+ if no failure
    edge(
      <U3>,
      <U3>,
      marks: "->",
      bend: 145deg,
      loop-angle: 0deg,
      label: text(size: 0.65em)[$1-alpha_3$],
      label-pos: 0.5,
      label-sep: 0.1em,
    ),

    // failures to Down (prob depends on age-since-maintenance)
    edge(<U0>, <D>, marks: "->", bend: 30deg, label: text(size: 0.65em)[$alpha_0$], label-sep: -0.92em),
    edge(<U1>, <D>, marks: "->", bend: 35deg, label: text(size: 0.65em)[$alpha_1$], label-sep: -0.92em),
    edge(<U2>, <D>, marks: "->", bend: 40deg, label: text(size: 0.65em)[$alpha_2$], label-sep: -0.92em),
    edge(<U3>, <D>, marks: "->", bend: 45deg, label: text(size: 0.65em)[$alpha_3$], label-sep: -0.92em),

    // repair + maintenance resets age to 0
    edge(<D>, <U0>, marks: "->", bend: 35deg, label: text(size: 0.65em)[$beta$], label-sep: 0.1em),

    // remain Down
    edge(
      <D>,
      <D>,
      marks: "->",
      bend: 145deg,
      loop-angle: 180deg,
      label: text(size: 0.65em)[$1-beta$],
      label-pos: 0.5,
      label-sep: 0.1em,
    ),
  )
}

// Gambler's ruin DTMC transition diagram
#let gambler-ruin-transition-diagram() = {
  diagram(
    spacing: 20pt,

    state((0, 0), label: $0$, name: <0>, tint: red.lighten(30%)),
    state((2.5, 0), label: $1$, name: <1>, tint: olive.lighten(85%)),
    state((5, 0), label: $2$, name: <2>, tint: olive.lighten(85%)),
    state((7.5, 0), label: $3$, name: <3>, tint: olive.lighten(85%)),
    state((10, 0), label: $4$, name: <4>, tint: olive.lighten(30%)),
    edge(
      <1>,
      <0>,
      marks: "->",
      bend: 45deg,
      label: text(size: 0.7em)[$q$],
      label-sep: 0em,
    ),
    edge(
      <2>,
      <1>,
      marks: "->",
      bend: 45deg,
      label: text(size: 0.7em)[$q$],
      label-sep: 0em,
    ),
    edge(
      <3>,
      <2>,
      marks: "->",
      bend: 45deg,
      label: text(size: 0.7em)[$q$],
      label-sep: 0em,
    ),
    edge(
      <1>,
      <2>,
      marks: "->",
      bend: 45deg,
      label: text(size: 0.7em)[$p$],
      label-sep: 0em,
    ),
    edge(
      <2>,
      <3>,
      marks: "->",
      bend: 45deg,
      label: text(size: 0.7em)[$p$],
      label-sep: 0em,
    ),
    edge(
      <3>,
      <4>,
      marks: "->",
      bend: 45deg,
      label: text(size: 0.7em)[$p$],
      label-sep: 0em,
    ),
    edge(
      <0>,
      <0>,
      marks: "->",
      bend: 145deg,
      loop-angle: 180deg,
      label: text(size: 0.7em)[$1$],
      label-pos: 0.5,
      label-sep: 0em,
    ),
    edge(
      <4>,
      <4>,
      marks: "->",
      bend: 145deg,
      loop-angle: 0deg,
      label: text(size: 0.7em)[$1$],
      label-pos: 0.5,
      label-sep: 0em,
    ),
  )
}
