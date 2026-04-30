# ADAM Directors Dashboard — manual QA checklist

Run this after every non-trivial change.

## 1. Cold open
- [ ] Double-click `index.html` in Windows Explorer → dashboard loads in demo mode.
- [ ] Top-right "Mode" chip reads `Demo mode` with a blue dot.
- [ ] Console has zero errors (F12 → Console).
- [ ] Footer mirrors the mode chip.

## 2. Live mode handshake (requires RunADAM.bat)
- [ ] Start `D:\ADAM\RunADAM.bat`; wait until `localhost:8300` responds.
- [ ] Reload dashboard → Mode chip reads `Live · localhost:8300` with green dot.
- [ ] Submitting intent from the conversational panel produces a packet with real BOSS score.
- [ ] Approving from the modal calls `POST /approve/{id}` and the row vanishes.

## 3. Agent mesh
- [ ] All 81 tiles rendered across 7 group cards.
- [ ] Hovering a tile pops a tooltip with agent name, status, CPU, mem, queue depth.
- [ ] Status changes pulse in over time (red tiles pulse).
- [ ] Mesh totals chip (top-right of panel) sums to 81.

## 4. Approval queue
- [ ] Five demo packets visible, sorted by score descending.
- [ ] Tier pills: 2× OHSHAT (red), 3× HIGH (orange).
- [ ] Clicking a row opens the detail modal.
- [ ] Modal shows dimension bars, alternatives, triggers, recommendation.
- [ ] Approve closes modal, removes row, toasts success, appends Flight Recorder event.
- [ ] Reject same behaviour with red toast.
- [ ] Modify does the same, with event type `director_modified`.

## 5. Director roster
- [ ] 5 cards rendered (CEO, CFO, Legal, Market, CISO).
- [ ] Per-director count pill shows correct number.
- [ ] Clicking a card filters the queue.
- [ ] Dropdown filter works identically.

## 6. Intent conversational panel
- [ ] Entering text and submitting adds a blue "you" bubble and a dark "adam" bubble with tier + composite.
- [ ] The irreversible checkbox bumps the composite by +15.
- [ ] Example chips populate the input.
- [ ] HIGH / OHSHAT intents produce a new queue entry with the right owning director.

## 7. Explain-Back panel
- [ ] Pasting an 8-character prefix of an intent_id returns a narrative.
- [ ] Narrative references the dimensions, the owning director, and the recommendation.
- [ ] Example chips work.

## 8. Digital Twin usage
- [ ] 4 twin cards render.
- [ ] Consultation bars proportional.
- [ ] Divergence cell changes colour above 1% and above 2%.

## 9. Flight Recorder tail
- [ ] Shows 10 latest events.
- [ ] New events append as pulse() runs (every 2s).
- [ ] Event sequence numbers monotonically increase.

## 10. Resize & responsive
- [ ] Dragging bottom-right of any panel resizes that panel only.
- [ ] Density slider resizes everything smoothly.
- [ ] At 1024px → 2×2. At 1023px and below → stacked column.
- [ ] At 360px (mobile emulation) → still readable, no horizontal scroll.
- [ ] At 2560px (4K) → grid widens, no absurd whitespace.

## 11. Accessibility
- [ ] Tab cycles through every interactive control in visual order.
- [ ] Enter on a queue row opens the modal.
- [ ] Escape closes the modal.
- [ ] Screen reader announces conversational bubbles (tested with Narrator).
- [ ] Focus ring visible on all focusable elements.

## 12. Print / export
- [ ] Ctrl-P → preview shows dashboard minus top bar, toolbar, footer, and action buttons.
- [ ] All four quadrants fit on the printed page without clipped text.

## 13. Regression
- [ ] `node qa/headless-smoke.js` prints 31/31 PASS.
