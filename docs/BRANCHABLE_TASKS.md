# Branchable-task inventory

A sweep of all 165 shipped tau-bench test tasks (115 retail, 50 airline) for conditionals
that could drive parametric branch-selection in the style of `gtau/branch.py`
(`RETAIL_KEYBOARD_EXCHANGE`, retail task 0). A task is **STATE-TESTABLE** when its
instruction's conditional is a predicate over regenerable DB content (variant
availability, prices, order status/payment, flight schedule/attributes), so a seeded
resampler can flip which branch of the golden fires while the oracle stays
construction-derived — both branch targets must already exist in the catalog
(we never synthesize entities). Other conditionals are **POLICY** (resolved the same
way every instance by the wiki), **BEHAVIORAL** (fallback is dialogue with no distinct
final DB state), or **AMBIGUOUS**.

Predicates for every EASY-graded candidate were verified against
`tau-bench/tau_bench/envs/retail/data/products.json` / `orders.json` (variant ids,
availability flags, prices quoted below are from the shipped data). Selected MEDIUM/HARD
predicates (5–9, 29, 30, 35, 45, 58, 60, 76, 88, 89, 90) were spot-verified too.

## Summary counts

| Class | Retail | Airline | Total |
|---|---|---|---|
| STATE-TESTABLE | 51 | 25 | 76 |
| POLICY | 16 | 11 | 27 |
| BEHAVIORAL | 15 | 5 | 20 |
| AMBIGUOUS | 7 | 4 | 11 |
| (no conditional) | 26 | 5 | 31 |
| **Total** | **115** | **50** | **165** |

By difficulty within STATE-TESTABLE: **EASY 14** (all retail), **MEDIUM 37** (29 retail
+ 8 airline), **HARD 25** (8 retail + 17 airline). Airline has zero EASY candidates:
every airline conditional routes through schedule selection, payment arithmetic, or an
empty-golden branch.

## STATE-TESTABLE candidates (EASY first)

Column key — *Pivot*: the DB field(s) a seeded resampler toggles/resamples.
*Shipped branch*: which branch the shipped data satisfies (and whether `task.actions`
covers it faithfully — it does unless noted). *k*: number of branches.

| Grade | Task | Conditional (gist) | Predicate (DB terms) | Pivot | Branch delta in golden | Shipped branch | k | Hazards |
|---|---|---|---|---|---|---|---|---|
| EASY | retail 0 | clicky keyboard; RGB else no backlight | available variant of 1656367028 {clicky, RGB, full size} exists | avail of 9025753381 | exchange target 9025753381 vs 7706410293 | fallback (9025753381 unavail) — **shipped spec** | 2 | none (the shipped spec) |
| EASY | retail 1 | same predicate; else exchange thermostat only | same as task 0 | avail of 9025753381 | item_ids/new_item_ids gain or drop the keyboard leg | fallback (thermostat-only) | 2 | item *list* changes, not just one target |
| EASY | retail 6 | lamp less bright; prefer battery > USB > AC | first available low-brightness variant of 6817146515 in pref order | avail of 7453605304 (battery), 9190635437 (USB), 1569765161 (AC) | exchange target walks the cascade | rung 1 (battery avail) → 7453605304 | 3 | water-bottle leg dropped by scripted confirmation (deterministic) |
| EASY | retail 7 | same, prefer AC > battery > USB | same pool, different order | same three variants | target walks cascade | rung 1 (AC avail) → 1569765161 | 3 | same as 6 |
| EASY | retail 8 | lamp brighter; prefer battery > USB > AC | first available high-brightness variant in pref order | avail of 1270145486 (battery), 9083642334 (USB), 7624783998 (AC) | target walks cascade | rung 2 (battery-high 1270145486 unavail) → 9083642334 | 3 | shipped data already exercises the fallback rung |
| EASY | retail 9 | same, prefer AC > battery > USB | same pool | same variants | target walks cascade | rung 1 → 7624783998 | 3 | same as 6 |
| EASY | retail 41 | jigsaw → easiest level, fewest pieces | argmin (difficulty, pieces) over available variants of 1808611083 | avail of 1096508426 (beginner/500/art); runner-up 9665100170 (beginner/1500) | modify target = argmin | argmin = 1096508426 ✓ golden | argmin (k = avail pattern) | address legs invariant |
| EASY | retail 42 | same + "if not shipped yet" | same argmin; plus order status pending | same; (order status = secondary pivot → no-op branch) | same | same | argmin | status pivot makes a no-op branch (grade jumps to HARD if used) |
| EASY | retail 44 | cheapest available desk lamp | argmin price over available variants of 6817146515 | avail of 5320792178 ($135.24); runner-up 1569765161 ($143.02) | modify target = argmin | argmin = 5320792178 ✓ golden | argmin | output '17.99' = price diff — flips with branch |
| EASY | retail 79 | exact 1000ml bottle; else different material ok | 2439754078 (1000ml steel red) of 8310926033 available | avail of 2439754078 | modify target 2439754078 vs a 1000ml other-material variant (1434748144 glass red — exists, shipped-unavailable) | **primary** (2439754078 avail) — opposite polarity to task 0 | 2 | resampler must force fallback variant available; "exact item" anchored to the other order's item |
| EASY | retail 83 | refund tablet to credit card; if not possible, GC | order #W9571698 original payment == credit card | order's payment_history method (shipped: gift_card_7250692) | return payment_method_id: CC vs gift_card_7250692 | fallback (paid by GC → CC refund impossible per policy) | 2 | pivot is an order field, not variant availability; "angry" tone rider is cosmetic |
| EASY | retail 97 | cheapest green bluetooth speaker | argmin price over available green variants of 4768869376 | avail of 2652637226 ($292.71) / 5967152432 ($292.71) — shipped-off; only 9440686670 ($298.91) on | modify target = argmin green | argmin trivially = 9440686670 ✓ golden | argmin | address leg invariant |
| EASY | retail 98 | same as 97 (ordering of requests differs) | same | same | same | same | argmin | same |
| EASY | retail 107 | t-shirt one size smaller, cotton; black if multiple colors | available XL cotton variants of 9523456873; black present? | avail of 2060066974 (black) vs 8124970213 (purple) | exchange target black vs purple | black present → 2060066974 ✓ golden | 2 | cardinality-tiebreak predicate (slightly richer than existence) |
| MEDIUM | retail 20 | pay upgrade diff with GC; if impossible, PayPal | gift_card_4332117 balance ≥ upgrade price diff | GC balance (numeric) | payment_method_id: GC vs PayPal on one big modify | GC branch | 2 | diff must be computed over 4-item upgrade; balance arithmetic |
| MEDIUM | retail 29 | shorter bamboo skateboard, pick most expensive | argmax price over available 28-inch bamboo variants of 1968349452 | prices/avail of 6843647669 / 6673921677 / 8176740019 | exchange target = argmax | argmax = 8176740019 ($208.60) ✓ | argmax | outputs are the three option prices — co-vary with resample |
| MEDIUM | retail 35 | 13-inch laptop; prefer i5 over i7, silver/black colors | preference cascade over available 13-inch variants of 4760268021 | avail of 5052031638, 6056040996, 1657832319 | modify target walks cascade | i5+silver → 5052031638 ✓ | k≈3 | "exact 13-inch twin" of owned 17-inch doesn't exist in catalog, so the outer conditional can never flip — only the cascade can |
| MEDIUM | retail 40 | apply GC to order if possible, else visa | gift_card balance ≥ order total | GC balance ($60 shipped) | modify_pending_order_payment target: GC vs credit_card_8897086 | fallback (60 < total) | 2 | output '60' is the GC balance itself |
| MEDIUM | retail 45 | canister vacuum; bagless *iff several options* | count of available canister variants of 1762337868 > 1 | avail flags of 1345513440 / 2872451762 / 7958300294 / 1304426904 | target: bagless 7958300294 vs the single available one | several (3 avail) → bagless ✓ | 2+ | output '9.89' = price diff; cardinality predicate |
| MEDIUM | retail 49 | exchange earbud to cheapest earbud from rest of order | argmin price among other earbud items in #W3470184 | prices of the order's earbud items | exchange target = argmin (1646531091 shipped) | argmin ✓ | argmin | predicate ranges over order contents, not one product's variants |
| MEDIUM | retail 52 | camera with maximum zoom, other specs same | argmax zoom over available variants of 8940227892 with same storage | avail of 9228757377 (10x SD) | exchange target | 9228757377 ✓ | argmax | shipped golden already bends "same specs" (24MP→30MP); toggling 9228757377 off leaves only 3x SD = degenerate no-op |
| MEDIUM | retail 56 | if not shipped, cancel purifier; can't → cheapest purifier, GC | order #W4284542 status pending; argmin purifier variant | order status + avail/prices of 3821016478 variants | modify to 9534205511 vs no action | pending → modify ✓ | 2–3 | no-op branch (see HARD note); partial-cancel leg is POLICY |
| MEDIUM | retail 58 | espresso 8 bar else 9 else 7 else none; laptop cheapest i7+ | available {1.5L, capsule} variant of 4354588079 at pressure 8/9/7 | avail of 3815173328 (9 bar 1.5L capsule) | coffee-machine leg present (target 3815173328) vs dropped from the 2-item exchange | 9-bar rung ✓ | nominal 4, **realizable 2** | 8-bar and 7-bar variants don't exist anywhere in the catalog — the famous cascade is mostly vacuous; laptop argmin (6017636844) is a second pivot; GC-else-CC payment leg |
| MEDIUM | retail 60 | blue earbuds, price ≤ current; *iff several*, no water resistance | count of available blue variants of 9924732112 with price ≤ owned | avail flags of the 4 available blue variants | target: 6077640618 vs the lone qualifying variant | several → 6077640618 ✓ | 2+ | output '242.92' = chosen price |
| MEDIUM | retail 64 | camera → highest-res waterproof within paid price | argmax resolution over available variants ≤ paid price | prices/avail of 3377618313 variants | exchange target = argmax | 6700049080 | argmax | shipped golden fires BOTH exchange_delivered and modify_pending with same args — annotation suspect |
| MEDIUM | retail 69 | return laptop; if can't return, cancel | order #W2417020 status delivered vs pending | order status | return_delivered vs cancel_pending (action name flips) | pending → cancel ✓ | 2 | status resample must stay policy-consistent (timestamps, fulfillments) |
| MEDIUM | retail 70 | helmet M/high-vent; blue if multiple colors | count of available {M, high} variants of 7765186836 by color | avail of blue vs other colors | exchange target color | blue → 9013366374 ✓ | 2+ | output '22.55' = pay-today diff |
| MEDIUM | retail 71 | backpack medium/polyester; grey if multiple colors | available {medium, polyester} variants; grey present? | avail of grey vs alternates | modify target | grey → 5917587651 ✓ | 2 | GC→PayPal payment dance is scripted but deterministic; desk-lamp leg dropped by same script |
| MEDIUM | retail 72 | same as 71 (request ordering differs) | same | same | same | same | 2 | same |
| MEDIUM | retail 74 | laptop i9; prefer 256GB SSD; prefer silver | cascade over available i9 variants of 4760268021 | avail of 3265035808 / 2913673670 / 8193934556 | modify target walks cascade | 3265035808 ✓ | k≈3 | second (cancel) leg invariant |
| MEDIUM | retail 76 | skateboard → maple/34/graphic; if unavailable, cancel order | 2343503231 {maple, 34in, graphic} available | avail of 2343503231 (shipped: False) | modify_pending_order_items vs cancel_pending_order on #W1242543 | fallback (cancel) ✓ | 2 | action name flips; fleece-jacket cancel leg is POLICY-fixed; grill-total output invariant |
| MEDIUM | retail 77 | perfume → maximum available size | argmax size over available woody/men variants of 6858788497 | avail of 3399869890 (100ml) | exchange target | 100ml avail → 3399869890 ✓ | 2 | no 50ml woody/men exists — toggling the 100ml off collapses to "no exchange" (shape change); new-order leg is POLICY |
| MEDIUM | retail 82 | refund pricier tablet to CC; if not possible, return everything to GC | order #W9571698 original payment == credit card | order payment method | return [6065192424] w/ CC vs return all 4 items w/ GC | fallback (paid GC) ✓ | 2 | item set changes across branches; "angry" rider behavioral |
| MEDIUM | retail 88 | bookshelf → 4 ft same material/color; else cancel order | 7373893106 {glass, white, 4ft} available | avail of 7373893106 (shipped: False) | modify to 7373893106 vs cancel #W8835847 | fallback (cancel) ✓ | 2 | action name flips; cancel reason scripted |
| MEDIUM | retail 89 | cheapest keyboard < $200 → exchange to it; else return | min price over available variants of 1656367028 < 200 | variant prices (cheapest shipped: 3616838507 @ $226.11; **no sub-$200 keyboard exists** — needs price resample) | exchange vs return (action flips) | fallback (return) ✓ | 2 | outputs ('226.11','tactile','white','full') describe the argmin — co-vary |
| MEDIUM | retail 90 | camera to 10x; unavailable → cancel "no longer needed"; avail but > $3000 → cancel "ordered by mistake" | 9228757377 {30MP,10x,SD} availability; its price vs 3000 | avail + price of 9228757377 | modify vs cancel(reason A) vs cancel(reason B) | avail & $3066.23 > 3000 → cancel "ordered by mistake" ✓ | 3 | branch determines the cancel *reason string*; price + availability are two coupled pivots |
| MEDIUM | retail 91 | e-reader: exchange to same item if available online, else return | availability flag of owned variant 9494281769 | avail of 9494281769 | exchange(9494281769→9494281769) vs return in #W3239882 | primary (available → self-exchange) ✓ | 2 | action name flips; skateboard/watch leg scripted by confirmation |
| MEDIUM | retail 99 | jigsaw +1000 pieces same difficulty; animal over art if both | availability of animal vs art candidates in 1808611083 | avail of 6245746168 (animal) vs 5546244844 (art) | one new_item_id inside a 2-item exchange | animal avail → 6245746168 ✓ | 2 | camera/bicycle legs invariant; payment-method rider behavioral |
| MEDIUM | retail 100 | same but art over animal | same pool, flipped preference | same | 5546244844 ✓ | same | 2 | pair with 99 — the two tasks are each other's branches |
| MEDIUM | retail 102 | metal watch; white if multiple colors | available metal variants of watch product by color | avail of white vs alternates | modify target 2407258246 | white ✓ | 2 | purifier + address legs invariant |
| MEDIUM | retail 103 | same (purifier lives in a different order) | same | same | same | same | 2 | pair with 102 |
| MEDIUM | retail 110 | tablet → cheapest | argmin price over available variants of tablet 2106335193's product | prices/avail | modify target = argmin | 2106335193 ✓ | argmin | golden also has 2 address writes (invariant legs) |
| MEDIUM | retail 111 | same (different source address) | same | same | same | same | argmin | pair with 110 |
| MEDIUM | airline 6 | cheapest economy, day after original | argmin price over ATL→PHL connections on 5/24 | flight prices/seat availability | flights list in update_reservation_flights | HAT110+HAT172 ✓ | argmin | route enumeration needed to derive golden |
| MEDIUM | airline 7 | same, EWR also acceptable | argmin over ATL→{PHL,EWR} | same + EWR legs | same | same | argmin | destination change would alter reservation destination — policy forbids; only PHL flights actually eligible |
| MEDIUM | airline 11 | pay with certificate; if > $100 wasted, GC+CC | cert value − trip price > 100 | certificate amount / flight prices | payment_methods list in book_reservation | fallback (waste > 100 → GC+CC) ✓ | 2 | flights copied from existing reservation (invariant); amounts arithmetic |
| MEDIUM | airline 19 | nonstop DTW↔JFK, arrive before 7am, cheapest economy | constrained argmin over schedule | flight times/prices | flights list + bag payment | HAT169/HAT033 ✓ | argmin | insurance fee-waiver leg is POLICY |
| MEDIUM | airline 20 | one-stop → nonstop | nonstop LAS→IAH exists on date | schedule (existence/times of nonstops) | flights list | nonstop exists ✓ | 2 | bag-refund leg refused by POLICY; golden keeps return leg unchanged |
| MEDIUM | airline 25 | book *second-cheapest* economy JFK→SFO 5/24 | 2nd-order statistic over itinerary prices | flight prices | flights + payment amount in book_reservation | ✓ | selection | cancel leg is POLICY-refused insistence; amount arithmetic |
| MEDIUM | airline 31 | cancel ATL→JFK dup; if not cancellable, cancel the other | cancellability (created_at/cabin/insurance) of the ATL→JFK reservation | that reservation's cabin/insurance/created_at | which reservation_id gets cancelled | shipped cancels 9HBUV8 | 2 | single cancel action, arg flips — cleanest airline candidate; verify which res is ATL→JFK before authoring |
| MEDIUM | airline 32 | rebook + add Kevin if total ≤ $500, else alone | 2 × per-pax price ≤ 500 | flight price | passengers list (2 vs 1) + payment amount | 2-pax ($348 ≤ 500) ✓ | 2 | certificate remainder non-refundable — arithmetic riders |
| HARD | retail 30 | tablet: exchange same item if available, else return + cancel charger | avail of owned tablet variant 3788616824 | avail of 3788616824 (shipped: False) | exchange vs return **and** the charger cancel_pending appears only on the return branch | fallback ✓ | 2 | action *count* changes; sneaker-return leg invariant; tracking-number output invariant |
| HARD | retail 36 | cheapest-options total ≤ $1131 → do it; else cancel | Σ argmin-price variants over 5 items ≤ 1131 | item prices across 5 products | 3-item modify vs cancel_pending | modify (fits) ✓ | 2 | outputs ('camera','481.5') derived from prices; sibling of 37/38 |
| HARD | retail 37 | same, threshold $1150 | same | same | same | modify ✓ | 2 | same |
| HARD | retail 38 | same, threshold $950 | same | same | same | **cancel** ✓ — 36/38 are the two branches shipped as separate tasks | 2 | free faithfulness check across the pair |
| HARD | retail 54 | exchange boots to same size/material *only if cheaper* | ∃ available same-size/material boots variant with price < paid | prices/avail of boots variants | an exchange action appears/disappears among cancels+returns | fallback (no exchange) ✓ | 2 | refund-total output; multi-order golden |
| HARD | retail 57 | cancel order iff refund can go to GC | order payment method == GC (and status pending) | order payment method | cancel_pending vs **empty golden** | shipped golden is empty | 2 | no-op branch = no write actions; oracle still distinct |
| HARD | retail 62 | speaker > $300 → drop it; add a < $100 speaker if one exists | speaker price vs 300; ∃ available speaker < 100 | speaker variant prices | shipped golden read-only (both sub-conditions dead-end via policy) | read-only ✓ | 3+ | policy interplay (can't cancel single item / can't add); sibling of 63 |
| HARD | retail 63 | same but < $300 threshold for the add | ∃ available speaker < 300 | speaker prices | modify to cheapest (2635605237) vs nothing | modify ✓ | 2 | output '1288.65' total arithmetic; pair with 62 |
| HARD | airline 0 | prefer direct; if multiple, lowest price; two certs else larger+card | itinerary price/availability ordering; cert-count policy | flight prices, seat availability | flights in book_reservation + payment split | ✓ | selection | booking arithmetic; cert leg is POLICY (one cert max) |
| HARD | airline 1 | later flight today, else earliest tomorrow; if BE can't modify → cancel w/ insurance | reservation cabin == basic_economy; else schedule selection | reservation cabin + schedule | cancel_reservation vs update_reservation_flights | BE → cancel ✓ | 2–3 | flipping cabin re-routes the whole task through a different conditional |
| HARD | airline 3 | fastest same-day return; pay with smallest gift card | argmin total duration over return itineraries; argmin GC balance | flight times; GC balances | flights list + payment_id | ✓ | selection | two independent pivots; duration arithmetic incl. stopovers |
| HARD | airline 8 | cheapest business RT; BE → cancel+rebook; minimize CC charge | itinerary prices; cabin==BE; refund-vs-rebook arithmetic | prices + cabin + cert/GC balances | cancel+book vs update; payment split amounts | cancel+book ✓ | 2+ | heavy payment arithmetic; outputs are the sums |
| HARD | airline 10 | cheapest direct RT NYC→West Coast; BE if cheaper | argmin over (airport, cabin, itinerary) | flight prices | book_reservation flights/cabin | ✓ | selection | passenger-removal leg is POLICY (cancel+rebook) |
| HARD | airline 14 | business upgrade for all if ≤ $600, else just Noah | upgrade cost arithmetic vs 600 (twice) | business-cabin prices of the 2 legs | update_reservation_flights appears (whom/whether) vs bags-only | neither fits → bags only ✓ | 3 | cabin is per-reservation, so "upgrade only Noah" is impossible by API — branch collapses to policy explanation |
| HARD | airline 16 | delayed-flight compensation | flight status == delayed (+ member/insurance gate); $50 × pax | flight status, passenger count | send_certificate(150) vs nothing | delayed → cert ✓ | 2 | amount derived (50×3); empty branch |
| HARD | airline 17 | date push + business ≤ $1000 total, else nothing | change cost arithmetic vs 1000 | cabin prices | updates vs **empty golden** | shipped golden empty (over budget) | 2 | no-op branch |
| HARD | airline 21 | nonstop ≤ $100 fee, else keep | ∃ nonstop on 5/17 with acceptable fee | schedule + prices | update vs empty golden | empty ✓ | 2 | no-op branch |
| HARD | airline 23 | insurance fee-waiver; budget $200 → economy return → economy both | change-cost arithmetic vs 200 | flight/cabin prices | update flights+cabin+bags vs partial vs none | economy-both ✓ | 3 | per-leg cabin impossible by API; pair with 24 |
| HARD | airline 24 | same but "if above budget, no changes" | same | same | updates vs empty golden | **empty** ✓ — 23/24 are shipped sibling branches | 2 | no-op branch |
| HARD | airline 27 | change M20IZO to nonstop *if available* | ∃ nonstop JFK→MCO on date | schedule | update_reservation_flights vs nothing | no nonstop → no update ✓ | 2 | cancel legs partially POLICY (one of two refused) |
| HARD | airline 28 | cancel all upcoming, proceed even without refund | per-reservation cancellability (created_at, cabin, insurance, flight status) | those attributes across 7 reservations | which subset of cancel_reservation calls appears | 3 of 7 cancellable ✓ | 2^k-ish | needs a policy evaluator as the predicate; action count varies |
| HARD | airline 33 | cancel reservations with any flight > 3h; upgrade rest to business | flight durations per reservation | scheduled times | cancel set + upgrade set | ✓ | k-way | duration arithmetic across whole profile |
| HARD | airline 34 | if BE, upgrade to economy first, then cancel | cabin == basic_economy per reservation | cabins of XEHM4B / 59XX6W | upgrade step inserted before cancel | XEHM4B BE → upgrade+cancel ✓ | 2 per res | sequence shape changes; mid-dialogue cost outputs |
| HARD | airline 41 | "booked 10 hours ago" — cancel if actually within 24h | reservation created_at within 24h of now | created_at timestamp | cancel_reservation vs read-only golden | >24h → refuse (read-only) ✓ | 2 | user-sim *lies* about the pivot — nice memorization trap; empty branch |
| HARD | airline 42 | cancel with refund iff insurance on reservation | reservation.insurance == "yes" | insurance flag of 3RK2T9 | cancel vs read-only golden | no insurance → refuse ✓ | 2 | cleanest airline pivot, but the pass branch is empty-golden |

## Per-candidate notes (EASY, all verified against shipped data)

**retail 0** — the shipped `RETAIL_KEYBOARD_EXCHANGE` spec. 9025753381 {clicky, RGB,
full} avail=False; fallback 7706410293 {clicky, none, full} avail=True. Thermostat leg
invariant. Reference shape for everything below.

**retail 1** — identical predicate, different fallback *behavior*: on False the keyboard
drops out of the exchange entirely (`item_ids=[4983901480]`, `new_item_ids=[7747408585]`).
Spec is a two-line variation of task 0's; the only new machinery is letting the
branch decide list membership instead of one list element. Shipped golden = fallback,
faithful.

**retail 6/7/8/9** — one family, four preference permutations over desk lamp
6817146515. Owned 8384507844 {white, medium, USB}. Low-brightness pool: battery
7453605304 ($150.01, avail), USB 9190635437 ($153.23, avail), AC 1569765161 ($143.02,
avail). High-brightness pool: battery 1270145486 (avail=False), USB 9083642334 (avail),
AC 7624783998 (avail). Each task's golden matches the first available rung of its
stated order — including task 8, where the shipped data already knocks out rung 1.
Toggling one availability bit walks the cascade; all targets in-catalog. The
water-bottle half of each instruction is dropped by a scripted confirmation exchange
(deterministic, no DB effect), so the end-state stays single-valued.

**retail 41/42** — jigsaw 1808611083, "easiest level, fewest pieces" = lexicographic
argmin (difficulty, pieces) over available variants: 1096508426 (beginner/500/art,
avail) wins; runner-up 9665100170 (beginner/1500/animals, avail). Toggle the winner to
flip. Task 42 adds an "if not shipped yet" guard — pending in shipped data; using order
status as a second pivot creates a no-op branch and bumps the grade.

**retail 44** — cheapest available lamp variant: 5320792178 $135.24; next 1569765161
$143.02. Golden matches. Hazard: output '17.99' is 153.23 − 135.24 and must be
re-derived per branch (the fallback diff is 10.21).

**retail 79** — the exact 1000ml item (2439754078, steel/red, avail=True) **is
available in shipped data, so the shipped golden covers the PRIMARY branch** — the
mirror image of task 0. The stated fallback ("allow the material to be different")
maps to 1434748144 {1000ml, glass, red}, which exists but ships unavailable; the
resampler must set it available when it toggles the primary off, exactly the
solvability-by-construction move `derive_golden` already makes.

**retail 83** — pivot is `orders["#W9571698"].payment_history[0].payment_method_id`
(shipped: gift_card_7250692). Policy: refunds go to original method or an existing GC,
so "refund to credit card" is possible iff the order was paid by that card. Branch
flips one arg of one return action. Sibling 82 is the same pivot with an item-set
change (return everything vs just the $989.70 tablet 6065192424); 84 resolves by
scripted confirmation instead (BEHAVIORAL).

**retail 97/98** — only one green speaker variant is available in shipped data
(9440686670 $298.91), making the argmin trivial; two cheaper greens (2652637226,
5967152432, both $292.71) ship unavailable. Toggling either on moves the argmin.
Address-change leg invariant. 98 differs only in request ordering.

**retail 107** — owned 9354168549 {red, XXL, cotton, crew}. One size smaller + cotton
= XL cotton: black 2060066974 (avail) and purple 8124970213 (avail). Multiple colors →
black, matching golden. Toggle black off → purple is the unique option and the
tiebreak clause deactivates.

## POLICY (conditional resolves identically every instance via wiki)

Retail: **10** (cross-order refund impossible → human), **11** (same → original
payment), **12** (PayPal refund of CC-paid order impossible → human), **25/26** (amex
refund of PayPal-paid order impossible), **28** (single-item cancel impossible),
**31/32** (refund/reorder lost item impossible; partial cancel impossible), **33/34**
(partial cancellation of pending order impossible → address change), **39** (agent
can't place orders), **50** (can't undo cancellation → human), **59** (agent can never
guarantee 5-day processing → cancel), **65** (cross-product exchange impossible —
golden is read-only), **66** (item→different-product change impossible → cascade ends
in cancel), **81** (partial cancel impossible → cancel whole orders).

Airline: **9** (one-certificate-per-reservation rule always forces the 3-booking plan),
**12** (non-cancellable per policy — golden read-only), **13** (partially-used
reservation unmodifiable → transfer), **15** (passenger count unchangeable; golden is
empty), **26** (one of two cancels refused by the 24h/insurance rules), **37** (delay
compensation requires change/cancel which the user refuses — read-only), **38**
(insurance not separately refundable → transfer), **39** (birthday isn't a covered
cancel reason — read-only), **47** ("phone rep approved it" doesn't override policy),
**48** (bereavement isn't an exception; read-only), **49** (>24h, no insurance —
read-only).

## BEHAVIORAL (fallback is dialogue; no branch-distinct end-state)

Retail: **5** (double-confirmation script fixes the end state), **18** (rethink →
same-item exchange), **21** (change of mind on confirmation), **24** (regret on
confirmation; Q&A outputs), **46/47** (wrong-order-id script; which vacuum is user-stated),
**67/68** (zip-code correction script), **84** (confirmation flips the choice), **92**
(withhold confirmation to add items), **93/94/95/96** ("if the agent asks which laptop"
disambiguation — user-supplied, not DB), **114** (reason revealed only if asked).

Airline: **18** (coercion/negotiation for BE cancel), **35/36** (insistence → transfer),
**45/46** (false passenger-count assertion script; certificate leg exists but the
task's conditionals are all dialogue).

## AMBIGUOUS

- retail **3/4** — "prefer polyester" cascade has no in-catalog alternative: purple/S/
  v-neck exists only in polyester (9647292434), so the preference can't branch without
  synthesizing a variant; t-shirt availability toggles also break the required output
  ('10' counts *available* variants: 10 of 12).
- retail **13** — shipped golden returns the same items twice with different payment
  methods; the intended single end-state is unclear (annotation suspect).
- retail **19** — "if you can only do one" ranges over order statuses, but the golden's
  choice logic (returns only the bottle) plus dual savings outputs leave multiple
  defensible end-states.
- retail **27** — same "if only one is possible" shape; why the returns fail isn't
  recoverable from the instruction alone.
- retail **61** — blue-earbud swap states no fallback; if the same-specs blue variant
  (8555936349) is toggled off the golden is underdetermined (sibling 60 fixes this
  with its "iff several" clause).
- retail **108** — "more fancy theme" is not a DB predicate.
- airline **22** — shipped golden contains two overlapping update_reservation_flights
  calls (2 flights, then 1); end-state intent unclear.
- airline **29** — "cancel all single-passenger reservations" but the shipped golden
  takes no write action; the cancellability × passenger-count interplay is unresolved.
- airline **30** — duplicate-day detection is state-testable in principle, but the
  instruction hardcodes the disambiguating cities/dates ("LAX on May 17, BOS on May
  22"), which would have to co-vary with any resample — instruction regeneration is out
  of scope for rung 2.
- airline **40** — compensation for a cancelled flight; golden is read-only, so either
  no shipped flight qualifies or the refusal is intended — can't tell which contract to
  regenerate.

## No conditional (not classified)

Retail: 2, 14, 15, 16, 17, 22, 23, 43, 48, 51, 53, 55, 73, 75, 78, 80, 85, 86, 87,
101, 104, 105, 106, 109, 112, 113.
Airline: 2, 4, 5, 43, 44.

## Cross-cutting observations

1. **Authored branch pairs already ship.** 36/37/38 (thresholds 1131/1150/950 — 36 and
   38 land on opposite branches), 62/63, retail 82/83/84, 99/100, 102/103, 110/111,
   5–9 (preference permutations), airline 23/24. A branch spec for one member can be
   faithfulness-checked against its sibling's shipped golden, the same way
   `test_fallback_reproduces_shipped_golden` uses task 0 — sometimes for *both*
   branches at once.
2. **Outputs couple to the pivot.** Wherever `task.outputs` quotes a price, diff, or
   option list (44, 60, 89, 29, 36–38, 45, 70, 40…), the user-sim's required outputs
   must be co-derived with the golden or the replay oracle and the output check will
   disagree across branches.
3. **Polarity varies.** Task 0 ships on its fallback branch; 79 and 91 ship on their
   primary. Specs shouldn't assume the shipped DB is the "unavailable" world.
4. **Catalog gaps silently kill branches.** 3/4 (no cotton twin), 58 (no 8- or 7-bar
   espresso variants anywhere), 35 (no 13-inch twin of the owned laptop), 77 (no 50ml
   woody/men) — always confirm the flip target exists before authoring, since the
   resampler may only toggle availability, never invent variants.
5. **Airline pivots skew HARD** — schedule/duration selection, payment arithmetic, and
   empty-golden branches. The gentlest entry points are 31 (which duplicate gets
   cancelled — single cancel, arg flip), 32 (passenger list by price threshold), and
   11 (payment split by certificate-waste threshold).
