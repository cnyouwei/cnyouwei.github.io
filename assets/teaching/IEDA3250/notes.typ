#import "style.typ": *
#import "figures.typ": *

#set document(
  author: ("Wei YOU",),
  date: auto,
  title: [IEDA3250 Stochastic Models],
)
#let logo-image = image("figures/UST_logo.svg", height: 2.5em)
#let emblem-image = image("figures/UST_emblem.svg", height: 1.5em)

#let text-size = 19pt
#set text(text-size)
#set page(
  paper: "presentation-16-9",
  margin: (left: 1.5em, right: 1.5em, top: 2.25em, bottom: 1.5em),
  header: context [
    #place(top + right, dx: 4mm, dy: 4mm)[#emblem-image]
  ],
  footer: context [
    #grid(
      columns: (8%, 1fr, 13%, 4%),
      align(left, text(size: text-size * 0.6, fill: accent-color, weight: "semibold")[#author-name()]),
      align(center, text(size: text-size * 0.6, fill: accent-color, weight: "semibold")[#current-section-titles()]),
      align(right, text(size: text-size * 0.6, fill: accent-color-light)[Updated: #date-str]),
      align(right, text(size: text-size * 0.6, fill: accent-color)[
        #counter(page).display("1", both: false)
      ]),
    )
  ],
  numbering: "1.",
  supplement: [Page],
)

#set heading(numbering: "1.", supplement: [Section])

#show heading.where(level: 1): set text(accent-color)
#show heading.where(level: 2): set text(accent-color-light)
#show heading.where(level: 3): set text(accent-color-light)

#show: frame-style(styles.thmbox, kind: "poll")
#show: frame-style(styles.thmbox, kind: "example")
#show: frame-style(styles.thmbox, kind: "definition")
#show: frame-style(styles.thmbox, kind: "proposition")
#show: frame-style(styles.thmbox, kind: "theorem")
#show: frame-style(styles.thmbox, kind: "lemma")

// style for bold text
#show strong: set text(fill: accent-color)

// this is necessary for references to theorems (by package theoretic) to work
#show ref: theoretic.show-ref

// package theoretic with custom style, default example is not numbered
// #let ex = theorem.with(
//   options: (color: oklch(65%, 0.15, 131deg)),
//   supplement: "Example",
//   kind: "example",
// )

// Start of Document

#titlepage(term: [Fall 2026], logo: logo-image)
#outlinepage(depth: 3)

// Numbering by section
#show: ratchet.with(
  reset-figure-kinds: (image, table, raw, "poll", "example", "definition", "theorem", "lemma", "proposition"),
)
//
// #set math.equation(numbering: "(1)")

#counter(page).update(1)

= Introduction

In modern Industrial Engineering practice, the central design challenge is to "optimize the system."
A decision maker must:
- allocate limited resources
- while balancing competing objectives.

#info(
  title: [Connection to IEDA3010 *Prescriptive Analytics*],
)[IEDA3010 translates real decision problems into optimization models---identify objectives and constraints, formulate linear/network/integer/dynamic programs, and solve for optimal policy.]

A typical constraint we see in IEDA3010 is a *budget constraint* $sum_i c_i y_i <= B$.
- *Interpretation*: producing quantity $y_i$ incurs unit cost $c_i$; the total spend across all decisions cannot exceed the budget $B$.

#warning(
  title: [Cost uncertainty in practice],
)[
  In practice, unit costs $c_i$ are _not fixed_.
  - They can vary with spot prices, surge incentives, supplier lead times, and congestion.
  - A deterministic budget constraint $sum_i c_i y_i <= B$ is often only an approximation; the true spend is random and may violate $B$ _unless we plan for risk_.
]

*Stochastic Models* extends the prescriptive workflow to environments where the _inputs_ and _system evolution_ are *random*:
- demand fluctuates, service times vary, failures occur, and travel times are uncertain.
As a result, the "right" decision is no longer optimized against a single deterministic scenario; it is optimized against _risk_, _service levels_, and _long-run performance_.

== Where Randomness Enters Engineered Systems

#example[ChatGPT (LLM platform)][
  - *Context*: an interactive, consumer-facing chat product that *streams* tokens. Each request has (i) a *prefill* stage that processes the full prompt and builds the KV-cache, then (ii) a *decode* stage that generates tokens one-by-one.
  - *Resource*: GPU compute + memory (KV-cache), concurrency / queue capacity.
  - *KPI*: Time to First Token (TTFT); Time Per Output Token (TPOT); p95/p99 end-to-end latency; error / rate-limit rejects.
  - *Decision*: admission control / rate limits; model routing (small vs large); batching & scheduling; token caps / truncation; autoscaling.
  #v(1em)
  - *Randomness*: bursty query arrivals; heterogeneous prompt lengths; variable output length (tokens); system load.
] <ex:GPT>

#example[Foodpanda (on-demand marketplace)][
  - *Context*: an on-demand marketplace matching customers, merchants (restaurants/shops), and couriers in real time; service is naturally *two-stage* (merchant prep + courier pickup/delivery) and demand peaks are strongly time-of-day and location dependent.
  - *Resource*: fleet size; driver hours; dispatch capacity; staging locations.
  - *KPI*: pickup-time p90/p95; on-time probability; utilization; empty miles.
  - *Decision*: dynamic pricing / incentives; repositioning; batching/stacking orders; service-region throttling.
  #v(1em)
  - *Randomness*: stochastic trip requests; travel-time variability (incidents/weather); spatio-temporal imbalance; cancellations/no-shows.
] <ex:Foodpanda>

#pagebreak()

#example[Zara (fast fashion inventory management)][
  - *Context*: new styles launch frequently; each style has a short selling window; stores receive frequent shipments from a centralized network.
  - *Resource*: limited store shelf/fixture space; DC throughput; nearshore production capacity; weekly shipment slots.
  - *KPI*: sell-through in first 7--14 days; stockout / lost-sales rate; markdown rate at season-end; inventory turns; freshness (time-on-floor).
  - *Decision*: (i) *initial allocation* of a new style across stores; (ii) *replenishment cadence* and cross-store rebalancing; (iii) small-batch "test then scale" production; (iv) markdown timing vs salvage.
  #v(1em)
  - *Randomness*: trend-driven, highly time-varying demand; size--color mix uncertainty; early-week sales signals; returns; occasional lead-time disruptions.
] <ex:Zara>


== Decisions under Uncertainty: Why Stochastic Models Matter
Across systems in @ex:GPT, @ex:Foodpanda and @ex:Zara
, the decision maker must act _before the randomness unfolds_:
- capacity is provisioned, fleets are positioned, and inventory is allocated days or weeks ahead.

#grid(
  columns: (1fr, 2fr),
  gutter: 1em,
  idea(title: [IEDA3010])[We optimize against *known inputs* (costs, demands, capacities).],
  idea(
    title: [IEDA4180 / 4331 / 4420 / 4510 / 4520],
  )[The inputs are *random*, and performance is driven by the *distribution* of outcomes, not just the mean.
    - Service Engineering (IEDA4180)
    - System Risk Management (IEDA4510)
    - Quantitative finance (IEDA4331, IEDA4520)
    - Pricing and Revenue Management (IEDA4420)
  ],
)

#figure(
  curriculum_map(),
  caption: [IEDA curriculum map: Stochastic Models in context],
)

#example[A deterministic plan says][
  - "Average demand is 100/day, so producing 100/day should meet demand."
  - "Average processing time is 3 minutes, so capacity of 20 jobs/hour should suffice."
  - "Utilization is 80%, so the system should have plenty of slack."
  These seem reasonable: the system appears to "keep up" with demand on a "typical day."
]

#warning[Planning based on a "average" is fragile, operational performance is driven by *variability*:
  - Demand arrives in *bursts*, not as a smooth flow.
  - A small fraction of jobs take *much longer* than the mean.
  - Rare disruptions (failures, congestion, weather) dominate tail risk.
]

=== Case study: Waiting-Time Paradox
#example[Waiting-time / inspection paradox][
  You arrive at a bus stop with a schedule that promises a bus every *20 minutes*.
  You wait... and wait.
  "Any second now," you tell yourself,
  "Surely any second."---and, at last, the bus arrives.

  It feels as if you always arrive one breath after the previous bus has gone.
]
#emoji.hands.raised Raise your hand if this has happened to you.

#poll[Bus wait-time][
  Buses are scheduled every 20 minutes. How long do you expect to wait for the next bus?
  #set enum(numbering: "A).")
  + Less than 10 minutes
  + 10 minutes
  + 10--20 minutes
  + More than 20 minutes
]

#question[
  Consider a simplified scanario where buses arrive *exactly* every 20 minutes. What is your expected waiting time until the next bus arrives?
]

#figure(
  inspection-paradox-plot(),
  caption: [Bus waiting: same mean headway, different typical waiting],
)

#idea(title: [Is it just bad luck?])[
  *How*: You are not sampling bus gaps uniformly---you are _sampling time_.
  - Long gaps occupy more time on the clock, so you are *more likely to arrive during a long gap* than a short one.
  - As a result, the gap you "observe" tends to be longer than a typical gap between buses.

  *Inspection paradox*: when interarrival times are variable, random inspections (your arrival time) are biased toward seeing longer intervals.

  *When*: Passengers experience longer waits _whenever_ interarrival times are *irregular*.
]

#info(title: [Results (to be proved later in the course)])[
  Suppose buses come "*every 20 minutes*", the mean _experienced_ waiting time depends on how _variable_ the arrivals are:
  - *always larger than 10 = 20/2 minutes*;
  - *equals 10 minutes* only when interarrival times are *perfectly deterministic*;
  - *equals 20 minutes (!)* for a realistic random bus arrival model.
  More on this in _renewal process_.
]

=== Case Study: Phantom Traffic Jam

#example[Phantom traffic jam][
  You are driving on a highway. The cars ahead suddenly brake. You crawl for *10 minutes*---
  "An accident," you tell yourself,
  "Surely an accident."---and then, almost magically, the road clears.

  _No crash. No cone. No closure._
  It feels like the jam came from nowhere: a *phantom jam*.
]

#emoji.hands.raised Raise your hand if this has happened to you.

#poll[Why do phantom traffic jams occur?][
  Suppose there is no accidents or bottlenecks, why do phantom traffic jams occur on highways?
  #set enum(numbering: "A).")
  + GPS disrupted.
  + Traffic accident on the opposite side.
  + Trump reelected.
  + A butterfly flapped its wings in Brazil.
]

#idea(title: [Catch the phantom!])[
  - When traffic is dense, tiny random disturbances (one driver hesitates, taps the brake, or leaves a slightly larger gap) get *amplified*.
  - The next driver reacts a bit _later_ and brakes a bit _harder_; the next one does the same. - Within seconds, a stop-and-go wave forms and _travels backward through the stream_.

  *Why*:
  The system *breaks* because it is operating near a _critical point_: there is not enough slack to absorb variability. A small fluctuation does not die out; it cascades into a macroscopic jam that persists long after the original disturbance is gone.
]

#example[My experience: Rubbernecking (a "gapers' delay")][
  There *is* an accident---but it's on the *opposite* side.
  My lanes are fully open. Still, traffic on my side suddenly slows because many drivers briefly look over and tap the brakes.
]

#warning[
  A highway designed for *average* traffic flow will inevitably operate near capacity during peak hours.
  In that regime, small random fluctuations in driving behavior (hesitation, braking, lane changes) amplify into *phantom jams*.

  *Possible solution:* _Reduce variability_.
  Automated vehicles smooth accelerations and shorten reaction lags, damping disturbances.
  (Why subway systems rarely "jam": they run on centralized control, scheduled interarrival times, and limited interaction variability.)
]

#memo[
  When system utilization is high, small variability is not "noise"---it becomes the *driver* of performance, which is why we need stochastic models. (More on this in _queueing theory_.)
]

=== Case Study: Pop Mart Blind-Box

#example[Blind-box drop: one decision, uncertain hype][
  A new collectible series is released in "blind boxes": you buy a sealed box without knowing which figure you will get.
  Some variants are common; a few are *rare*.

  On release day, demand can be calm---or it can explode after a viral post.
  If you under-supply, everything sells out instantly and customers leave frustrated (and scalpers celebrate).
  If you over-supply, the hype dies, shelves clog, and the "rare chase" feeling evaporates.
]

#emoji.hands.raised Raise your hand if you have ever tried to get a "drop" item that sold out.

#question[
  Suppose last month you sold 10,000 boxes *on average* per drop.
  For the next drop, should you simply produce 10,000 again?
]

#idea(title: [The "hype tail"])[
  Two drops can have the same *average* demand but feel totally different:
  - *Stable world*: demand is consistently near 10,000.
    Ordering "around 10,000" is usually fine.
  - *Hype world*: most drops are modest, but occasionally demand spikes overnight (celebrity post, viral unboxing).
  - *What hurts more*?
    - Selling out instantly (lost revenue, angry fans, bad UX).
    - Overstocking (dead inventory, weaker brand momentum).
]

#warning[
  Blind-box products create *two layers of randomness*:
  - demand uncertainty (hype, time-of-day spikes, influencer shocks), and
  - "mix" uncertainty (which variants customers chase, and how fast the rare ones get depleted).

  Planning based on an average can be systematically wrong because what matters is the probability of *extreme* outcomes.
]

#idea(title: [This is a *newsvendor problem* in collectibles industry])[
  You must commit inventory *before* the demand spike reveals itself.
  Stochastic thinking forces you to _plan for the distribution_ (how often a viral surge occurs), not just the mean.

  More on this in _IEDA4420 Dynamic Pricing and Revenue Management_.
]

== Stochastic Model: Basic Concepts

Any realistic model of a real-world phenomenon must _account for randomness_. In many engineered systems, the quantities we care about---demand, processing times, failures, travel times---are not predictable in advance, but exhibit inherent variation that materially affects performance.

#definition[Stochastic model][
  A *stochastic model* is a mathematical model of a system in which one or more inputs, mechanisms, or state variables are *random*.
  It specifies:
  - the *random quantities* that drive the system and the evolving *state* of the system,
  - and the induced *distribution* of performance metrics (e.g., delay, stockouts, reliability).
]

#pagebreak()

#definition[Random variable][
  A *random variable* $X$ is a rule that converts an outcome of an random experiment into a number (or vector).
  It lets us treat uncertain quantities like demand as mathematical objects.
]

#definition[Distribution][
  The *distribution* of a random variable describes how likely different values are.
  - Discrete case: a probability mass function (PMF) $p(x)$.
  - Continuous case: a density (PDF) $f(x)$.
  - A universal summary is the CDF: $F(x) = bb(P)(X <= x)$.
]

#definition[Expectation and variance][
  - *Mean*: $bb(E)[X] = integral_(-infinity)^(infinity)x f(x)"d"x$,  the long-run average level.
  - *Variance*: $"Var"(X) = bb(E)[(X - bb(E)[X])^2]$,  how spread out outcomes are around the mean.
]

#idea[
  Random variables are the _building blocks_ of stochastic models:
  - each one encodes an uncertain quantity of interest (e.g., demand, service time, failures).

  By *connecting* multiple random variables through the system's operational logic (flows, routing, and orders), we obtain a *time-evolving* description of the system.
  In other words, uncertainty does not appear as isolated "noise"---it *propagates through time* and across components.
  _Naturally, we organize a time-indexed family of random variables to describe this evolution. This object is a *stochastic process*._
]

#definition[Stochastic process][
  A *stochastic process* is a family of random variables ${X(t): t in cal(T)}$ indexed by $t$,
  where the index set $cal(T)$ often represents *time*.
  It models how a random quantity evolves, so we can reason about trajectories, long-run behavior, and event probabilities.
]<def:stochastic-process>

#example[Applications of stochastic processes][
  *Fields*: biology, chemistry, ecology, neuroscience, physics, signal processing, control theory, information theory, computer science, telecommunications, and financial markets.
  - Growth of a bacterial population (*over time*)
  - Electrical current fluctuating (*over time*) due to thermal noise
  - Movement of a gas molecule (*over time*) (_Brownian motion_)
  - Arrival of customer orders to an online store (*over time*)
  - Queue length / waiting time in a service system (*over time*)
  - Inventory level under replenishment and random demand (*over time*)
  - Machine up/down state with failures and repairs (*over time*)
  In these settings, observations are not viewed as independent data points.
  Instead, they are *time-coupled* random quantities that evolve with the system's dynamics.
]

#pagebreak()

== Overview of Topics
- *Discrete-time stochastic processes* (time in steps: days, jobs, decisions)
  - *Discrete-time Markov chains (DTMCs)*: state transitions each step.
    - Gambler's ruin; random walk with absorbing boundaries.
  - *Martingales*: "fair game" processes and what they imply about predictability.
    - Why no betting system beats a fair game (without edge).
- *Continuous-time stochastic processes* (time on the clock: seconds, minutes, hours)
  - *Counting / renewal processes*: modeling event arrivals over time.
    - Customer orders, calls, ride requests.
  - *Continuous-time Markov chains (CTMCs)*: random transition times between states.
    - Machine failure/repair (birth--death models).
- *Queueing systems* (arrivals + service + congestion dynamics)
  - Hospital/clinic patient flow; call-center waits; platform latency under load.
- *Decision-making under uncertainty*
  - *Markov decision processes (MDPs)*: optimize when the system state is random and evolving.
    - Inventory control and replenishment under random demand.

#pagebreak()

= Markov Chains
== Simple Random Walk <sec:random-walk>

Many IE systems evolve by repeating the same pattern:
#align(center)[
  *state today* + *random net change* = *state tomorrow*.
]

The key point is that randomness is not a one-off shock---it arrives again and again, and its effects *accumulate* over time.

#example[Platform growth][
  A platform's trajectory can also look like "many small daily wins and losses."
  - *State*: $X_n$ = cumulative user base (or a running product "health score").
  - *Randomness*: some days bring organic growth; other days bring churn (or incidents).
  - *Net change*: $xi_(n+1)$ = net gain (growth minus churn) on day $n+1$.
  - *Question*: Will we eventually "take off" past a target level, or drift down to a critical level?
]

#example[Gambler's bankroll][
  A gambler plays the same game repeatedly. Each round she either wins \$1 or loses \$1.
  - *State*: $X_n$ = bankroll after $n$ rounds.
  - *Randomness*: each round is a win/loss (think: "good day" vs "bad day").
  - *Net change*: $xi_(n+1) in {+1, -1}$ is the increment in round $n+1$ ($+1$ = win, $-1$ = loss).
  - *Questions*: Starting with $i$ dollars, what is the chance of bankruptcy before reaching $N$ (cashing out)?
    How long does it take (on average) to either go broke or cash out?
]

#question[
  In these examples, what is the *one number* you would carry forward from today to tomorrow?
  - The *state* $X_n$ is a compact summary of "where the system is now,"
  - The *net change* $xi_(n+1)$ determines what happens next.
]

#idea(title: [One-step dynamics])[
  The operational logic is the same across settings:
  - We observe the current state $X_n$.
  - A new random increment $xi_(n+1)$ arrives (demand shock, overrun, churn, etc.).
  - The next state is updated by addition: $X_(n+1) = X_n + xi_(n+1).$
]

#question[
  There are a few core questions we can ask about "state + random increment" systems:

  1. *Is there a systematic drift / trend?*
    - What is the average net change $bb(E)[xi_n]$?

  2. *What happens in the long run?*
    - Does the state $X_n$ tend to grow, shrink, or hover around a typical level?
    - If there is *no* upward/downward drift, what happens eventually?
      - Will we hit zero (bankruptcy, stockout, failure)?
      - Will we reach a high target (takeoff, success)?

  3. *How fast do critical events occur?*
    - How long does it take to hit key thresholds (on average, or with high probability)?
]

=== Definition of Simple Random Walk

To formalize the repeated "state + random increment" structure, we start with the simplest possible dynamic model: the *simple random walk*.

#info(title: [Refresher: Independent and identically distributed (i.i.d.)])[
  A sequence of random variables $X_1, X_2, dots$ is *i.i.d.* if it satisfies two properties:

  - *Identically distributed*: all $X_n$ share the same distribution.
    - _Intuition_: each step is generated by the *same mechanism* (same coin, same demand model, same service-time law).

  - *Independent*: knowing past values gives no information about future ones.
    - _Intuition_: the randomness "resets" each time; there is no dependence across periods.
]

In a simple random walk, the increments $xi_1, xi_2, dots$ are i.i.d.:
- Each step has the same win/loss probabilities, and one step does not influence the next.


#definition[Simple random walk][
  A *simple random walk* is a discrete-time stochastic process ${X_n : n >= 0}$ defined by:

  - *Initial state*: $X_0 = 0$.
  - *Update rule*:
    $
      X_(n+1) = X_n + xi_(n+1),
    $ <eq:state-update>
    where the increments $xi_1, xi_2, dots$ are *i.i.d.* with
    $
      bb(P)(xi_n = +1) = p, quad bb(P)(xi_n = -1) = q eq.def 1 - p.
    $
  #figure(
    random-walk-transition-diagram(),
    caption: [State transition diagram of simple random walk.],
  ) <fig:random-walk-transition-diagram>
] <def:simple-random-walk>

#question(title: [
  In plain language, what does the parameter $p$ control?
])[
  Recall that $p$ is the probability of an "up" step. The *trend* of the walk:
  - $p > 1/2$: "up" steps are more likely (upward drift).
  - $p = 1/2$: no systematic trend (fair game).
  - $p < 1/2$: "down" steps are more likely (downward drift).
]

=== Properties of Simple Random Walk
To formalize the intuition about trends and long-run behavior, we compute the *mean* and *variance* of the state $X_n$ after $n$ steps.

#proposition[Simple random walk mean and variance][
  For a simple random walk ${X_n}$ with step probability $p$:
  - *Mean*: $bb(E)[X_n] = (2p - 1)n.$
  - *Variance*: $"Var"(X_n) = 4 p q n = 4p(1-p) n.$
] <prop:random-walk-mean-var>

#proof[@prop:random-walk-mean-var][
  By linearity of expectation and i.i.d. increments,
  #nonum(
    $
      bb(E)[X_n] = bb(E)[sum_(i=1)^n xi_i] = sum_(i=1)^n bb(E)[xi_i] = n bb(E)[xi_1].
    $,
  )
  Since $bb(E)[xi_1] = (+1) dot p + (-1) dot q = p - q = 2p - 1,$ we have $bb(E)[X_n] = n(2p - 1).$

  For the variance, since the $xi_i$ are independent,
  #nonum(
    $
      "Var"(X_n) = "Var"(sum_(i=1)^n xi_i) = sum_(i=1)^n"Var"(xi_i) = n"Var"(xi_1).
    $,
  )
  Now, $bb(E)[xi_1^2] = (+1)^2 dot p + (-1)^2 dot q = p + q = 1,$ so
  #nonum(
    $
      "Var"(xi_1) = bb(E)[xi_1^2] - (bb(E)[xi_1])^2 = 1 - (2p - 1)^2 = 4 p q = 4p(1-p).
    $,
  )
  Therefore, $"Var"(X_n) = n"Var"(xi_1) = 4 p q n = 4p(1-p) n$.
]

#pagebreak()

#example[Symmetric random walk][
  A simple random walk with $p = 1/2$ is called a *symmetric random walk*. @prop:random-walk-mean-var[-] implies that,
  - the symmetric random walk has zero mean $bb(E)[X_n] = 0$;
    - On average, the state tends to stay around zero.
  - but variance that *grows linearly* with time: $"Var"(X_n) = n$.
    - The position of the state becomes _more and more spread out_ over time.
  Even when there is no systematic trend, the walk does *not* sit still.
  Random fluctuations accumulate ($"Var"(X_n) = n$), so the state can wander far away and hit critical thresholds.
]

#question[
  What is the distribution of the state?
]
Because $xi_1, xi_2, dots, xi_n in {+1,-1}$, the position $X_n = sum_(i=1)^n xi_i$ is determined by _how many_ "$+1$ steps" occurred.
Let
#nonum(
  $
    N_n eq.def sum_(i=1)^n bb(1)(xi_i = +1) tilde "Binomial"(n, p),
  $,
)
be the number of $+1$ increments among the first $n$ steps. From @eq:state-update, we have
#nonum(
  $
    X_n = X_(n-1) + xi_n = (X_(n-2) + xi_(n-1)) + xi_n = sum_(i=1)^n xi_i = (+1) N_n + (-1) (n - N_n) = 2 N_n - n.
  $,
)

#conclusion(title: [$X_n$ has a *shifted-and-scaled binomial* distribution])[
  #nonum(
    $
      bb(P)(X_n = x)
      =
      binom(n, (n + x)/2) p^((n + x)/2) q^((n - x)/2),
    $,
  )
  for values $x$ such that $x in {-n, -n+2, dots, n}$; otherwise $bb(P)(X_n = x)=0$.
]

#info(title: [Refresher: Central Limit Theorem (CLT)])[
  A sequence of random variables $xi_1, xi_2, dots$ is *i.i.d.*, each with mean $mu$ and variance $sigma^2 < infinity$.
  Then, as $n -> infinity$, the *standardized sum* converges to the standard normal distribution:
  #nonum(
    $
      Z_n eq.def (sum_(i=1)^n xi_i - n mu) / (sigma sqrt(n)) arrow.double bb(N)(0,1).
    $,
  )
]

#example[Application: The long-run behavior of $X_n$ via CLT][
  In a simple random walk with step probability $p$, we have $bb(E)[xi_i] = 2p - 1$ and $"Var"(xi_i) = 4 p q$.
  By the Central Limit Theorem, as $n -> infinity$,
  #nonum(
    $
      Z_n eq.def (X_n - n(2p - 1)) / (2 sqrt(p q n)) arrow.double bb(N)(0,1) quad "hence" quad X_n approx bb(N)(n(2p - 1), 4 p q n).
    $,
  )
]

#question[
  Will a simple random walk hit a fixed target level $T$ (can be positive or negative)?
  - In practice, $T$ is often a *threshold* (e.g., $0$ for bankruptcy, $N$ for successful cashout).
]

#definition[Hitting Time][
  The *hitting time* $tau_a$ of a level $a$ is the _first time the process touches $a$_:
  $
    tau_a eq.def min{ n >= 0 : X_n = a }.
  $ <eq:hitting-time>
] <def:hitting-time>

*Intuition*: How random walks evolve depends on whether the walk has a *drift*.

#example[Upward drift ($p > 1/2$): certainly hits positive targets][
  Intuitively, the walk will eventually hit any fixed *positive* target $a > 0$ because it tends to go up.
  Formally, the mean step is
  $bb(E)[xi_1] = p - q = 2p - 1 > 0$.

  By the *(strong) law of large numbers*,
  #nonum(
    $
      (X_n)/n = (1/n) sum_(i=1)^n xi_i arrow.double bb(E)[xi_1] = 2p - 1 > 0
      quad "as" quad n -> infinity.
    $,
  )

  This says that, with probability $1$, the ratio $X_n/n$ eventually stays close to $2p-1$.
  In particular, along almost every sample path, $X_n$ grows roughly linearly and hence $X_n -> infinity$.
  Therefore, for any fixed $a>0$, the walk must satisfy $X_n >= a$ for all sufficiently large $n$.

  Equivalently, the event "$X_n < a$ for all $n$" has probability $0$, i.e.
  #nonum(
    $
      bb(P)(tau_a < infinity) = 1.
    $,
  )
]

#example[Negative drift ($p < 1/2$): may never hit a positive target][
  When $p < 1/2$, the mean step is negative:
  $bb(E)[xi_1] = 2p - 1 < 0$. By the law of large numbers,
  #nonum(
    $
      (X_n)/n arrow.double 2p - 1 < 0
      quad "as" quad n -> infinity,
    $,
  )
  so along almost every sample path, $X_n$ eventually trends downward and $X_n -> -infinity$.

  #warning[
    This does *not* mean the walk can never reach a positive target $a>0$.
    It can still get lucky early and jump up to $a$.
    The point is: there is a *strictly positive* chance it drifts down forever *without ever* reaching $a$.
  ]
]
#example[Casino game where the house has a small edge][
  Think of $X_n$ as your net winnings after $n$ bets in a game with a small house advantage.
  - Your goal is to reach a wealth target $a>0$ before going broke.
  - You *might* succeed with an early streak of wins.
  - But with negative drift, there is always a nonzero (often substantial) chance you *never* reach $a$ and instead slowly bleed down.

  *Question:* How likely is it to ever hit $a>0$ when the drift is negative ($p < 1/2$)?

  *Answer (without proof here)*:
  The probability is *less than 1* and decays _exponentially_ in $a$:
  #nonum(
    $
      bb(P)(tau_a < infinity) = (p/q)^a, quad q eq.def 1 - p.
    $,
  )

  *Interpretation*: hitting a target *against the drift* requires a sustained run of "up" steps.
  The farther the target, the more extreme the required streak, so the success probability becomes exponentially small.
]

#experiment[
  Discuss the case with *downward drift* ($p < 1/2$).
]

#poll[Hitting probabilities under symmetric random walk][
  Consider a *symmetric* random walk ($p = 1/2$) starting at $X_0 = 0$, so there is *no systematic drift*.

  What is the probability of hitting a fixed target $a>0$?

  #set enum(numbering: "A).")
  + Probability 0.
  + Probability strictly between 0 and 1.
  + Probability 1.
]

#info(title: [Hitting time under symmetric random walk (without proofs)])[
  Consider a *symmetric* random walk ($p = 1/2$) starting at $X_0 = 0$.

  - It hits every fixed level (positive or negative) *with probability 1*:
    #nonum(
      $
        bb(P)(tau_(+a) < infinity) = bb(P)(tau_(-a) < infinity) = 1, quad forall a > 0.
      $,
    )

  - But it can take a *very long* time; in fact, the expected hitting time is *infinite*:
    #nonum(
      $
        bb(E)[tau_(+a)] = bb(E)[tau_(-a)] = infinity, quad forall a > 0.
      $,
    )
]

#idea(title: [Drunkard's walk])[
  A classic interpretation of the *symmetric* random walk ($p = 1/2$) is a "drunkard" taking steps left or right at random.

  - There is *no drift*: on average the drunkard does not prefer either direction.
  - But there is *no stability* either: randomness accumulates, so the position keeps wandering.

  #info(title: [Two surprising facts])[
    - *Certain eventual hitting*: the drunkard will eventually stumble onto any fixed location $+a$ or $-a$ with probability $1$.
    - *No typical hitting time*: while hitting is certain, the expected time to hit $a$ is _infinite_.
  ]

  *IE translation*: "No trend" is not the same as "safe."
  Without drift, the system still explores extremes; buffers and controls determine whether those extremes are acceptable.
]

The same "drunkard" behaves very differently once you change the dimension:
- *1D*: steps left/right --- a drunken ant living on a rope.
- *2D*: steps on a grid --- a drunken human wandering in city blocks.

#align(center)[
  #figure(
    random-walk-2d-transition-diagram(),
    caption: [State transition diagram of a simple random walk in two-dimensional space.],
  )
]

#info(title: [Fun fact: drunkard's walk in higher dimensions])[
  - *1D (drunken ant) and 2D (drunken human)*:
    - With probability $1$, the drunkard returns to the starting point infinitely many times,
    - and will eventually visit any fixed location (given enough time).
    - Such states are called *recurrent*.

  - *3D and higher (drunken bird)*:
    - With probability $< 1$, the drunkard ever returns to the starting point.
    - In fact, there is a nonzero chance they wander off and *never* come back.
    - Such states are called *transient*.

  #warning[
    Adding an extra degree of freedom (moving in 3D instead of 2D) makes "getting lost forever" possible.
    This is one of the most famous *phase transitions* in stochastic models.
  ]
]

#pagebreak()
== Discrete-Time Markov Chains
Many engineered systems evolve in *discrete time steps*:
at time $n$, the system updates its _state_, denoted as $X_n$, according to a (possibly) _random rule_.

- To understand the dynamics of the system, a simplest model would probably be to assume that the $X_n$ are independent random variables, but often such an assumption is clearly unjustified.
  - For instance, starting at some time suppose that $X_n$ represents the price of one share of some security, such as Google, at the end of n additional trading days. Then it certainly seems unreasonable to suppose that the price at the end of day $n + 1$ is independent of the prices on days $n, n − 1, n - 2$ and so on down to day $0$.
However, it might be reasonable to suppose that the price at the end of trading day $n + 1$ depends on the previous end-of-day prices only through the price at the end of day $n$.

In this section, we study a central model for such dynamics: *discrete-time Markov chains (DTMCs)*.

=== From Random Walk to Markov Chains

In @sec:random-walk, we saw a canonical example of a discrete-time stochastic process: the *simple random walk*.

#success(title: [Recap: Simple random walk])[
  - *State* $X_n$:
    - *Discrete time-steps*: evolves in discrete time steps $n = 0, 1, 2, dots$,
    - *Discrete state-space*: takes integer values $X_n in bb(Z)$.
  - *Update rule*: $X_(n+1) = X_n + xi_(n+1)$
    - *Independent increments*: the increments $xi_1, xi_2, dots$ are i.i.d. and take values in ${-1, +1}$.
]

#question[
  What is the *minimum* information you need to predict the distribution of $X_(n+1)$?

  #idea(title: [The punchline])[
    Once you know the *current state* $X_n$, the _detailed past_ no longer matters.

    - If $X_n = i$, then
      $bb(P)(X_(n+1) = i+1) = p$
      and
      $bb(P)(X_(n+1) = i-1) = q eq.def 1 - p$,
      regardless of how you got to $i$.
  ]
]

This "memoryless" property is the defining feature of the so-called *Markov chains*:
#align(center)[
  *Markov property*: _Given the present, the future does not depend on the detailed past._
]

#info(title: [Refresher: conditional probability (what does $bb(P)(A mid(|) B)$ mean?)])[
  Conditional probability formalizes "probability *given* that we know $B$ happened." <page:conditional-probability>

  *Events.*
  For events $A$ and $B$ with $bb(P)(B) > 0$, define
  #nonum(
    $
      bb(P)(A mid(|) B) eq.def (bb(P)(A inter B)) / (bb(P)(B)).
    $,
  )

  *Two immediate consequences* (use these constantly):
  - *Multiplication rule*:
    #nonum(
      $
        bb(P)(A inter B) = bb(P)(A mid(|) B) bb(P)(B).
      $,
    )
  - *Law of total probability* (partition by disjoint cases $B_1, dots, B_m$):
    #nonum(
      $
        bb(P)(A) = sum_(k=1)^m bb(P)(A mid(|) B_k) bb(P)(B_k).
      $,
    )
]

#info(title: [Conditional probability for random variables: "conditional distribution"])[
  For discrete random variables $X,Y$, conditioning on "$Y=y$" means conditioning on the event ${Y=y}$.
  If $bb(P)(Y=y) > 0$, define
  #nonum(
    $
      bb(P)(X=x mid(|) Y=y) eq.def (bb(P)({X=x} inter {Y=y})) / (bb(P)({Y=y})).
    $,
  )
  So, *knowing $Y=y$ changes the distribution of $X$*.

  For the simple random walk, the Markov property can be expressed as:
  #nonum(
    $
        & bb(P)(X_(n+1) = j mid(|) X_n = i, X_(n-1) = i_(n-1), dots, X_0 = i_0) \
      = & bb(P)(X_(n+1) = j mid(|) X_n = i) \
      = & cases(
            p & "if" j = i + 1,
            q & "if" j = i - 1,
            0 & "otherwise."
          )
    $,
  )
]


#pagebreak()
Let $cal(S)$ denote the *state space* of the process (the set of all possible states).
// - *Example*: In the simple random walk, $cal(S) = bb(Z)$ (the integers).
#definition[Discrete-Time Markov Chain (DTMC)][
  A discrete-time stochastic process (c.f. @def:stochastic-process) ${X_0, X_1, X_2, dots}$ is called a *discrete-time Markov chain (DTMC)* if, for every $n >= 0$ and all states $i_0, i_1, dots, i, j in cal(S)$,
  #nonum(
    $
      bb(P)(X_(n+1) = j mid(|) X_n = i, X_(n-1) = i_(n-1), dots, X_0 = i_0)
      =
      bb(P)(X_(n+1) = j mid(|) X_n = i).
    $,
  )
] <def:DTMC>

We focus on simpler _time-homogeneous_ cases where the step mechanism does not change with $n$.
#definition[Time-homogeneous DTMC][
  A DTMC is called *time-homogeneous* if there is a table of *one-step transition probabilities*
  #nonum(
    $
      P_(i j) eq.def bb(P)(X_(n+1) = j mid(|) X_n = i), quad i, j in cal(S), quad "that does not depend on" n.
    $,
  )
  The matrix $P = (P_(i j))_{i j in cal(S)}$ is called the *transition matrix* of the DTMC.
] <def:time-homogeneous-DTMC>

#warning(title: [Markov is about the *state representation*])[
  Not all stochastic processes are Markov *in the variables you happen to observe*.

  *Example (CGA is not "memoryless"):*
  Your CGA at the end of year $n$ certainly matters for predicting next year's CGA,
  but it is *not* enough information by itself:
  - Two students can have the same current CGA but very different *accumulated credits*,
    so the same future semester grade will move their CGA by different amounts.
  - Therefore, the distribution of next year's CGA depends on more than just the current CGA---it depends on *how you got there* (via credit history).

  *Key lesson:*
  A process can fail to be Markov because the "state" is missing information.

  *How to fix it (state augmentation):*
  If you define the state as
  #align(center)[(1) *total grade points so far* and (2) *total credits so far*,]
  then the next update depends only on this _augmented state_ plus the next semester's outcome.
]

#example[Random walk as a DTMC][
  #grid(
    columns: (1fr, 1fr),
    [
      - *State space*: $cal(S) = bb(Z)$.
      - *Randomness*: walk left with probability $p$ or right with probability $q$.
      - *Transitions*: from state $i$,
        - go to $i+1$ with probability $p$,
        - go to $i-1$ with probability $q eq.def 1 - p$.
    ],
    [
      - *Transition matrix*:
      #v(0.5em)
      #nonum(
        $
          P = #h(1.5em)
          mat(
            gap: #0.9em,
            mark(dots.down, tag: #<r1>), mark(dots.down, tag: #<c2>), mark(dots.down, tag: #<c3>), mark(dots.down, tag: #<c4>), mark(dots.down, tag: #<c5>), mark(, tag: #<c6>), mark(, tag: #<c7>);
            mark(dots.down, tag: #<r2>), q, 0, p, 0, 0, ;
            mark(dots.down, tag: #<r3>), 0, q, 0, p, 0, dots.down;
            mark(, tag: #<r4>), 0, 0, q, 0, p, dots.down;
            mark(, tag: #<r5>), , dots.down, dots.down, dots.down, dots.down, dots.down;
          )
          #annot(<r1>, pos: left, dx: -1em, leader-stroke: 0em, leader-tip: none, leader-toe: none)[$-2$]
          #annot(<r2>, pos: left, dx: -1em, leader-stroke: 0em, leader-tip: none, leader-toe: none)[$-1$]
          #annot(<r3>, pos: left, dx: -1em, leader-stroke: 0em, leader-tip: none, leader-toe: none)[$0$]
          #annot(<r4>, pos: left, dx: -1.25em, leader-stroke: 0em, leader-tip: none, leader-toe: none)[$1$]
          #annot(<r5>, pos: left, dx: -1.25em, leader-stroke: 0em, leader-tip: none, leader-toe: none)[$2$]
          #annot(<r1>, pos: top, dy: -0.7em, leader-stroke: 0em, leader-tip: none, leader-toe: none)[$-3$]
          #annot(<c2>, pos: top, dy: -0.7em, leader-stroke: 0em, leader-tip: none, leader-toe: none)[$-2$]
          #annot(<c3>, pos: top, dy: -0.7em, leader-stroke: 0em, leader-tip: none, leader-toe: none)[$-1$]
          #annot(<c4>, pos: top, dy: -0.7em, leader-stroke: 0em, leader-tip: none, leader-toe: none)[$0$]
          #annot(<c5>, pos: top, dy: -0.7em, leader-stroke: 0em, leader-tip: none, leader-toe: none)[$1$]
          #annot(<c5>, pos: top, dx: 1.45em, dy: -0.7em, leader-stroke: 0em, leader-tip: none, leader-toe: none)[$2$]
          #annot(<c5>, pos: top, dx: 2.9em, dy: -0.7em, leader-stroke: 0em, leader-tip: none, leader-toe: none)[$3$]
        $,
      )
    ],
  )
  #align(center)[
    #random-walk-transition-diagram(),
  ]
]

#memo[
  The row of the transition matrix $P$ each sum to 1:
  #nonum(
    $
      sum_(j in cal(S)) P_(i j) = 1, quad forall i in cal(S).
    $,
  )
  This is because from any state $i$, the process must transition to *some* state $j$ in the next step. Hence, the probabilities over all possible $j$ must add up to 1.
]

#definition[Stochastic matrix][
  A (right / row) *stochastic matrix* is a _square matrix_ of nonnegative real numbers, with each row summing to 1. The transition matrix $P$ of a DTMC is always a stochastic matrix.
]

#example[Machine up/down as a DTMC][
  #grid(
    columns: (1fr, 1fr),
    [
      - *State*: $X_n in {U, D}$ = machine is *Up* / *Down* at day $n$.
      - *Randomness*: If the machine is down, a technician performs repairs with probability $alpha$; otherwise, the machine may fail with probability $beta$.
      - *Transitions* (time-homogeneous):
        - $U -> D$ w.p. $alpha$ (failure),
        - $D -> U$ w.p. $beta$ (repair),
        - otherwise it stays.
    ],
    [
      - *Transition matrix*:
      #v(0.5em)
      #nonum(
        $
          P = #h(1.5em)
          mat(
            gap: #0.9em,
            mark(1-alpha, tag: #<r1>), mark(alpha, tag: #<c2>);
            mark(beta, tag: #<r2>), 1-beta;
          )
          #annot(<r1>, pos: left, dx: -1em, leader-stroke: 0em, leader-tip: none, leader-toe: none)[$U$]
          #annot(<r2>, pos: left, dx: -1.9em, leader-stroke: 0em, leader-tip: none, leader-toe: none)[$D$]
          #annot(<r1>, pos: top, dy: -0.5em, leader-stroke: 0em, leader-tip: none, leader-toe: none)[$U$]
          #annot(<c2>, pos: top, dy: -0.78em, leader-stroke: 0em, leader-tip: none, leader-toe: none)[$D$]
        $,
      )
      - *Transition diagram:*
      #align(center)[#machine-up-down-transition-diagram()]
    ],
  )
]

*Remarks:*
- Again, we see that the rows of the transition matrix sum to 1.
- A state can have transitions to itself (e.g., machine stays up or down).


#question[
  In the machine example, what if the failure risk depends on
  "days since last maintenance"?

  #warning(title: [${U, D}$ is no longer Markov])[
    If we keep the state space $cal(S) = {U, D}$, then the one-step transition
    $bb(P)(X_(n+1)=D mid(|) X_n=U)$ is *not* well-defined, as we would have to know *how long* the machine has been running since the last maintenance.

    In other words, the transition probabilities depend on the *history* (an "age" variable),
    not just on whether the machine is currently up or down.
  ]

]

#idea(title: [Augment the state to restore the Markov property])[
  Add a clock-like variable: "days since last maintenance."

  A simple augmented state space is
  $cal(S)^+ = {U_0, U_1, U_2, U_3, D}$, where
  - $U_k$: machine is *Up* and it has been $k$ days since the last maintenance,
  - $D$: machine is *Down*.

  With this augmentation, the next-day behavior depends only on the *current* augmented state,
  so the process becomes Markov again. The transition diagram is illustrated below:
  #align(center)[
    #machine-maintenance-augmented-state-diagram()
  ]
]

#example[Gambler's ruin][
  #grid(
    columns: (2.7fr, 1fr),
    [
      Consider a gambler who, at each play of the game, either wins \$1 with probability $p$ or loses \$1 with probability $q = 1 − p$. If we suppose that our gambler quits playing either when he goes broke or he attains a fortune of \$4, then the gambler's fortune is a Markov chain with state space $cal(S) = {0, 1, 2, 3, 4}$, where state $i$ represents $\$i$.
      #align(center)[
        #gambler-ruin-transition-diagram()
      ]
    ],
    [
      #v(0.5em)
      #nonum(
        $
          P = #h(1.5em)
          mat(
            gap: #1em,
            mark(1, tag: #<r1>), mark(0, tag: #<c2>), mark(0, tag: #<c3>), mark(0, tag: #<c4>), mark(0, tag: #<c5>);
            mark(q, tag: #<r2>), 0, p, 0, 0;
            mark(0, tag: #<r3>), q, 0, p, 0;
            mark(0, tag: #<r4>), 0, q, 0, p;
            mark(0, tag: #<r5>), 0, 0, 0, 1;
          )
          #annot(<r1>, pos: left, dx: -1em, leader-stroke: 0em, leader-tip: none, leader-toe: none)[$0$]
          #annot(<r2>, pos: left, dx: -1em, leader-stroke: 0em, leader-tip: none, leader-toe: none)[$1$]
          #annot(<r3>, pos: left, dx: -1em, leader-stroke: 0em, leader-tip: none, leader-toe: none)[$2$]
          #annot(<r4>, pos: left, dx: -1em, leader-stroke: 0em, leader-tip: none, leader-toe: none)[$3$]
          #annot(<r5>, pos: left, dx: -1em, leader-stroke: 0em, leader-tip: none, leader-toe: none)[$4$]
          #annot(<r1>, pos: top, dy: -0.7em, leader-stroke: 0em, leader-tip: none, leader-toe: none)[$0$]
          #annot(<c2>, pos: top, dy: -0.7em, leader-stroke: 0em, leader-tip: none, leader-toe: none)[$1$]
          #annot(<c3>, pos: top, dy: -0.7em, leader-stroke: 0em, leader-tip: none, leader-toe: none)[$2$]
          #annot(<c4>, pos: top, dy: -0.7em, leader-stroke: 0em, leader-tip: none, leader-toe: none)[$3$]
          #annot(<c5>, pos: top, dy: -0.7em, leader-stroke: 0em, leader-tip: none, leader-toe: none)[$4$]
        $,
      )
    ],
  )
]

#definition[Absorbing states][
  A state that, once entered, is never left is called an absorbing state.  In the gambler's ruin example, states $0$ and $4$ are absorbing states.
]

#example[Inventory chain: replenishment with a reorder point][
  Let $X_n$ be the *end-of-day* inventory after day $n$, and let $D_(n+1)$ be the demand on day $n+1$.


  $(s,S)$-policy:
  - If $X_n <= s$, we place an order so that the *start-of-day* inventory becomes $S$.
  - If $X_n > s$, we order nothing.
  - Assume replenishment order arrives before demand on day $n+1$ is realized.

  The dynamics can be written compactly as
  #nonum(
    $
      X_(n+1)
      =
      cases(
        (X_n - D_(n+1))^+ & "if" X_n > s,
        (S - D_(n+1))^+ & "if" X_n <= s.
      ), quad "where" quad x^+ eq.def max{x, 0}
      =
      cases(
        x & "if" x > 0,
        0 & "if" x <= 0,
      ).
    $,
  )
  So $(X_n)_(n >= 0)$ is a DTMC on the state space $cal(S) = {0, 1, dots, S}$.
]

#pagebreak()
Suppose $s=1$ and $S=5$, and demand takes values $0,1,2,3$ with
#nonum(
  $
    bb(P)(D_(n+1)=0)=0.3, quad
    bb(P)(D_(n+1)=1)=0.4, quad
    bb(P)(D_(n+1)=2)=0.2, quad
    bb(P)(D_(n+1)=3)=0.1.
  $,
)
- *States*: $cal(S) = {0, 1, 2, 3, 4, 5}$.
- *One-step transition matrix*:
#nonum(
  $
    P =
    mat(
      gap: #0.9em,
       // row 0
      mark(0, tag: #<r0>), mark(0, tag: #<c1>), mark(0.1, tag: #<c2>), mark(0.2, tag: #<c3>), mark(0.4, tag: #<c4>), mark(0.3, tag: #<c5>);
       // row 1
      mark(0, tag: #<r1>), 0, 0.1, 0.2, 0.4, 0.3;
       // row 2
      mark(0.3, tag: #<r2>), 0.4, 0.3, 0, 0, 0;
       // row 3
      mark(0.1, tag: #<r3>), 0.2, 0.4, 0.3, 0, 0;
       // row 4
      mark(0, tag: #<r4>), 0.1, 0.2, 0.4, 0.3, 0;
       // row 5
      mark(0, tag: #<r5>), 0, 0.1, 0.2, 0.4, 0.3;
    )
    #let labL = annot.with(pos: left, dx: -1.1em, leader: false)
    #let labT = annot.with(pos: top, dy: -0.7em, leader: false)
    // row labels
    #labL(<r0>)[$0$]
    #labL(<r1>)[$1$]
    #labL(<r2>)[$2$]
    #labL(<r3>)[$3$]
    #labL(<r4>)[$4$]
    #labL(<r5>)[$5$]
    // column labels (tagged on first row)
    #labT(<r0>)[$0$] // column 0 label anchored at (0,0)
    #labT(<c1>)[$1$]
    #labT(<c2>)[$2$]
    #labT(<c3>)[$3$]
    #labT(<c4>)[$4$]
    #labT(<c5>)[$5$]
  $,
)

#idea(title: [Why rows $0$ and $1$ look the same])[
  If $X_n in {0,1}$, the policy replenishes to $5$ *before* demand arrives.
  Therefore, starting from $0$ or $1$ has the same next-day distribution as starting from $5$.
]

#question[
  If we start with $X_0 = 5$, what is the distribution after 1 day and 2 days?
]

Define the state distribution row vector
#nonum(
  $
    mu^((n)) eq.def (mu^((n))_j)_(j=0,1,2,3,4,5),
    quad mu^((n))_j eq.def bb(P)(X_n=j).
  $,
)

With $X_0=5$ we have
#nonum(
  $
    mu^((0)) = (0, 0, 0, 0, 0, 1).
  $,
)
By the Kolmogorov update $mu^((n+1)) = mu^((n)) P$,
#nonum(
  $
    mu^((1)) = mu^((0)) P = (0, 0, 0.1, 0.2, 0.4, 0.3).
  $,
)
and one more step gives
#nonum(
  $
    mu^((2)) = mu^((1)) P = (0.05, 0.12, 0.22, 0.28, 0.24, 0.09).
  $,
)

#memo[
  This is the DTMC workflow in one line:
  *model the policy* $arrow.double$ *write $P$* $arrow.double$ *forecast via* $mu^((n)) = mu^((0)) P^n$.
]

#question[
  Profit application:
  Suppose the store earns \$12 per unit sold and pays \$2 per unit carried (per day).
  - What is the *long-run* average profit per day under $(s,S)=(1,5)$?
  - How should we choose $(s,S)$ to maximize long-run profit?
]


=== Chapman–Kolmogorov Equations: Multi-Step Transitions

#question[
  We already know the *one-step* rule:
  $ P_(i j) = bb(P)(X_(n+1)=j mid(|) X_n=i) $ <eq:one-step-transition>

  What if you need a *two-step* forecast:
  $bb(P)(X_(n+2)=j mid(|) X_n=i)$?
]

#idea(title: [The intermediate state trick])[
  To go from $i$ to $j$ in two steps, the chain must pass through *some* intermediate state $k$ at time $n+1$.

  *Trick:* Use the law of total probability,
  and then use the Markov property to "cut" the dependence.
]

#pagebreak()
*Two-step transition probabilities:*
For any states $i, j in cal(S)$, and any intermediate step $k in cal(S)$,
#nonum(
  $
    bb(P)(X_(n+2)=j mid(|) X_n=i) & =
                                    sum_(k in cal(S))
                                    bb(P)(X_(n+2)=j, X_(n+1)=k mid(|) X_n=i) \
                                  & =
                                    sum_(k in cal(S))
                                    bb(P)(X_(n+2)=j mid(|) X_(n+1)=k, X_n=i)
                                    bb(P)(X_(n+1)=k mid(|) X_n=i) \
                                  & = sum_(k in cal(S))
                                    bb(P)(X_(n+2)=j mid(|) X_(n+1)=k)
                                    bb(P)(X_(n+1)=k mid(|) X_n=i) \
                                  & = sum_(k in cal(S)) P_(i k) P_(k j).
  $,
)
- The first equality is the *law of total probability*, summing over all possible intermediate states $k$ at time $n+1$.
- The second equality uses the definition of conditional probability.
- The third equality uses the *Markov property* to eliminate dependence on $X_n=i$ when conditioning on $X_(n+1)=k$.

#proposition[Two-step transitions by matrix squaring][
  If $P$ is the one-step transition matrix, then the two-step transition matrix is
  #nonum(
    $
      P^((2)) = P dot P = P^2 = mat(delim: "[", P_11, P_12, dots, P_(1J); P_21, P_22, dots, P_(2J); dots.v, dots.v, dots.down, dots.v; P_(I 1), P_(I 2), dots, P_(I J);) dot mat(delim: "[", P_11, P_12, dots, P_(1J); P_21, P_22, dots, P_(2J); dots.v, dots.v, dots.down, dots.v; P_(I 1), P_(I 2), dots, P_(I J);),
    $,
  )
  with entries $P_(i j)^((2)) = sum_(k in cal(S)) P_(i k) P_(k j)$.
]

#example[Sanity check: random walk returns in two steps][
  For a simple random walk on $bb(Z)$ with $bb(P)(xi=+1)=p$ and $bb(P)(xi=-1)=q$,
  starting from $0$ the only way to return to $0$ in 2 steps is
  "up then down" or "down then up".

  #nonum(
    $bb(P)(X_2 = 0 mid(|) X_0=0)
    = p q + q p = 2 p q.$,
  )
]

#question[
  How to compute the $n$-step transition probabilities $bb(P)(X_(m+n)=j mid(|) X_m=i)$?
]

#poll[$n$-step transition probabilities][
  Given the one-step transition matrix $P$, how to compute the $n$-step transition matrix $P^((n))$?

  #set enum(numbering: "A).")
  + $P^n$ (matrix multiplication).
  + $n P$ (scalar multiplication).
  + $P + P + dots + P$ (matrix addition).
]

#definition[$n$-step transition probabilities][
  For a time-homogeneous DTMC on state space $cal(S)$, define
  #nonum(
    $
      P_(i j)^((n)) eq.def bb(P)(X_(m+n)=j mid(|) X_m=i),
      quad n=0,1,2,dots
    $,
  )
  which does not depend on $m$.
]

The *Chapman--Kolmogorov equations* provide a method for computing $n$-step transition probabilities.

#definition[Chapman--Kolmogorov equations][
  For any $m, n >= 0$ and any states $i, j$,
  $
    P_(i j)^((m+n))
    =
    sum_(k in cal(S)) P_(i k)^((m)) P_(k j)^((n)).
  $ <eq:chapman-kolmogorov>
]

#proof[Equation @eq:chapman-kolmogorov][
  Fix an arbitrary start time $r$ and condition on the *intermediate* state $X_(r+m)$.
  Using the law of total probability,
  #nonum(
    $
      P_(i j)^((m+n)) & = bb(P)(X_(r+m+n)=j mid(|) X_r=i) \
                      & = sum_(k in cal(S))
                        bb(P)(X_(r+m+n)=j, X_(r+m)=k mid(|) X_r=i) \
                      & =
                        sum_(k in cal(S))
                        bb(P)(X_(r+m+n)=j mid(|) X_(r+m)=k, X_r=i)
                        bb(P)(X_(r+m)=k mid(|) X_r=i) \
                      & = sum_(k in cal(S))
                        bb(P)(X_(r+m+n)=j mid(|) X_(r+m)=k)
                        bb(P)(X_(r+m)=k mid(|) X_r=i),
    $,
  )
  where the last line follows from the _Markov property_: given $X_(r+m)=k$ the future does not depend on the earlier history.
  Finally, by time-homogeneity (shift-invariance),
  #nonum(
    $
      bb(P)(X_(r+m)=k mid(|) X_r=i) = P_(i k)^((m)),
      quad
      bb(P)(X_(r+m+n)=j mid(|) X_(r+m)=k) = P_(k j)^((n)).
    $,
  )

  Substituting these into the sum gives @eq:chapman-kolmogorov.
]

#memo[
  Let $P$ be the one-step transition matrix. By Chapman--Kolmogorov equations, we have the matrix multiplication rule:
  #nonum(
    $
      P^((m+n)) = P^((m)) dot P^((n)) = mat(delim: "[", P^((m))_11, P^((m))_12, dots, P^((m))_(1J); P^((m))_21, P^((m))_22, dots, P^((m))_(2J); dots.v, dots.v, dots.down, dots.v; P^((m))_(I 1), P^((m))_(I 2), dots, P^((m))_(I J);) dot mat(delim: "[", P^((n))_11, P^((n))_12, dots, P^((n))_(1J); P^((n))_21, P^((n))_22, dots, P^((n))_(2J); dots.v, dots.v, dots.down, dots.v; P^((n))_(I 1), P^((n))_(I 2), dots, P^((n))_(I J);), quad forall m,n >= 0.
    $,
  )
  In particular, taking $n=1$ and iterating gives the familiar "matrix power" representation:
  #nonum(
    $
      P^((n)) = P^((n-1)) dot P = P^((n-2)) dot P dot P = dots.c = P^n, quad n=0,1,2,dots
    $,
  )
  Once you know $P$, every multi-step transition probability is an entry of $P^n$.
  In this sense, the full evolution of a time-homogeneous DTMC is encoded in its one-step transition matrix $P$.
]

#question[
  So far, we have focused on *point-to-point* transitions.
  Often in application, we don’t care about the exact path along which the system evolves, but rather the *distribution* of the state.

  - *Example:* in gambling, we do not care how we got to our current fortune, only (the probability of) how much money we have now.

  - *Question:* How does the distribution of the state evolve day by day?
]

Define the *state distribution row vector*
#nonum(
  $
    mu^((n)) eq.def (mu^((n))_j)_(j in cal(S)),
    quad
    mu^((n))_j eq.def bb(P)(X_n = j),
    quad n=0,1,2,dots
  $,
)

#theorem[Discrete-time Kolmogorov forward equation][
  Let $(X_n)_(n>=0)$ be a time-homogeneous DTMC with one-step transition matrix $P$.
  Then the one-step distribution update is
  #nonum(
    $
      mu^((n+1)) = mu^((n)) P,
      quad n >= 0,
    $,
  )
  equivalently, componentwise,
  #nonum(
    $
      mu^((n+1))_j = sum_(i in cal(S)) mu^((n))_i P_(i j), quad j in cal(S).
    $,
  )

  Iterating yields the $n$-step distribution
  #nonum(
    $
      mu^((n)) = mu^((0)) P^n, quad n=0,1,2,dots
    $,
  )
  (with $P^0$ the identity matrix).
] <thm:discrete-kolmogorov-forward>

#pagebreak()

#proof[@thm:discrete-kolmogorov-forward][
  Fix any $j in cal(S)$. By the law of total probability,
  #nonum(
    $
      mu^((n+1))_j
      = bb(P)(X_(n+1)=j)
      = sum_(i in cal(S)) bb(P)(X_(n+1)=j, X_n=i).
    $,
  )
  Then factor the joint probability:
  #nonum(
    $
      bb(P)(X_(n+1)=j, X_n=i)
      = bb(P)(X_(n+1)=j mid(|) X_n=i) bb(P)(X_n=i)
      = P_(i j) mu^((n))_i.
    $,
  )
  Summing over $i$ gives
  #nonum(
    $
      mu^((n+1))_j = sum_(i in cal(S)) mu^((n))_i P_(i j),
    $,
  )
  which is exactly the matrix identity $mu^((n+1)) = mu^((n)) P$.
  Iterating over $n$ yields
  #nonum(
    $mu^((n)) = mu^((n-1)) P = mu^((n-2)) P^2 = dots.c = mu^((0)) P^n.$,
  )
]

#example[Machine up/down (cont.)][
  State space $cal(S) = {U, D}$ with ordering $(U, D)$.

  *Transitions*:
  - $U -> D$ w.p. $alpha$, so $U -> U$ w.p. $1-alpha$.
  - $D -> U$ w.p. $beta$, so $D -> D$ w.p. $1-beta$.

  #nonum(
    $
      P =
      mat(
        1-alpha, alpha;
        beta, 1-beta;
      )
    $,
  )

  #question[
    Suppose the machine is *up* in day $0$, i.e., $mu^((0)) = (1, 0)$.
    What is the probability it is *down* after 1 day? after 2 days?
  ]
]

#pagebreak()
*After 1 day:*
#nonum(
  $
    mu^((1)) = mu^((0)) P = (1,0) P = (1-alpha, alpha) quad arrow.double quad bb(P)(X_1=D) = mu^((1)) bold(1)_D = alpha
  $,
)
so $$.

*After 2 days:*
#nonum(
  $
    mu^((2)) = mu^((1)) P = (1,0) P^2, "where"
    P^2 =
    mat(
      (1-alpha)^2 + alpha beta, alpha(2 - alpha - beta);
      beta(2 - alpha - beta), (1-beta)^2 + alpha beta;
    ).
  $,
)
Thus,
#nonum(
  $
    bb(P)(X_2=D)
    = mu^((0)) P^2 bold(1)_(D) = (1,0) P^2 bold(1)_(D)
    = (1-alpha)alpha + alpha(1-beta)
    = alpha(2 - alpha - beta).
  $,
)
Here, $bold(1)_(D)$ is the _column vector_ with $1$ in the $D$ component and $0$ elsewhere.

#v(1em)
- What if the distribution at time $0$ is $mu^((0)) = (1/2, 1/2)$?

#pagebreak()

=== Limiting behavior of DTMCs

asdasd
