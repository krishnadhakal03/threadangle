# Phase 3A Long-Form MVP Draft

Title concept: **I Used AI to Audit My Bills in 5 Minutes**

Draft status: script and scene plan only. Do not render the full long-form MP4 until approved.

Cost/privacy guardrails:
- Use free/local resources only.
- Do not use ElevenLabs, RunwayML, or paid API credits.
- Use local/demo data only.
- Do not use real personal bills, Gmail, bank data, passwords, or private documents.
- Do not modify Day4 assets or Day4 generators.

## Draft Script

### Scene 1 - Hook
Narration:
Most people think they spend about 86 dollars a month on subscriptions. But when the charges are actually itemized, the reality can be way higher. So in this video, I am going to show you a simple five-minute AI bill audit you can run with demo data first, then repeat with your own numbers privately.

On-screen:
Most people think: $86/mo
Reality can be higher

Visual:
Big contrast card based on the short-form proof style. Use quick number pop motion and no stock footage.

### Scene 2 - Build The Inventory
Narration:
Start by building a plain inventory of recurring charges. You do not need bank access or email access. Just list the service, the monthly price, what it is for, and whether you still use it. The goal is not perfection. The goal is to get the leaks into one readable place.

On-screen:
Service | Monthly | Category | Still use?

Demo rows:
Netflix $22.99 Entertainment Yes
Hulu $17.99 Entertainment Maybe
Spotify $11.99 Music Yes
Gym $39.99 Fitness No
Phone $95 Utilities Yes
Cloud $9.99 Storage Maybe

Visual:
Browser spreadsheet mock. Rows reveal quickly. Cursor moves down the amount column.

### Scene 3 - Type The AI Audit Prompt
Narration:
Then paste the table into an AI assistant and ask for a practical audit. The prompt is: Analyze these recurring expenses. Find overlaps, cheaper alternatives, and bills worth renegotiating.

On-screen prompt:
Analyze these recurring expenses.
Find overlaps, cheaper alternatives,
and bills worth renegotiating.

Visual:
Local browser AI assistant mock. Prompt types on screen. No login, no real provider, no private data.

### Scene 4 - AI Audit Reasoning
Narration:
Now look for reasoning, not magic. You want the AI to explain what it flagged and why. In this example, it sees two entertainment subscriptions, one unused gym charge, a phone bill that is high enough to negotiate, and a cloud plan that could probably be downgraded.

On-screen:
Overlap: Netflix + Hulu
Unused: Gym marked No
Renegotiate: Phone at $95
Downgrade: Cloud storage

Visual:
AI result panel reveals sections one by one. Keep text large enough for mobile.

### Scene 5 - Phone Bill Negotiation Workflow
Narration:
For the phone bill, turn the audit into an action step. Ask AI for a short call script. The script should ask for loyalty discounts, lower plans, autopay discounts, and retention offers. Then compare the final price, not just the headline plan.

On-screen:
Ask for:
Loyalty discount
Lower plan
Autopay discount
Retention offer

Sample call line:
Can you check whether I qualify for a lower monthly plan or retention offer?

Visual:
Browser mock with a simple call-script card and checklist. Cursor motion taps through the checklist.

### Scene 6 - Savings Summary
Narration:
In this demo audit, the possible savings are 53 dollars a month. That is 636 dollars a year. This is not guaranteed savings. It is a checklist of places to verify before the next bill hits.

On-screen:
Possible savings
$53/month
$636/year
Example audit

Visual:
Dominant proof card. Hold long enough to read. Captions below the card and away from numbers.

### Scene 7 - CTA
Narration:
Comment AUDIT and I will send the full prompt and checklist. Save this for your next bill day.

On-screen:
COMMENT AUDIT
FULL PROMPT + CHECKLIST
Save for bill day

Visual:
Clean CTA card, same visual system as short-form POC. No fade.

## Scene Plan

Target length: 5:00-6:00.

| Scene | Target Time | Purpose | Visual Type | Motion |
|---|---:|---|---|---|
| 1. Hook | 0:00-0:35 | Frame the spending gap and promise the tutorial | Contrast card + browser teaser | Number pop, quick hard cuts |
| 2. Inventory | 0:35-1:35 | Show how to build the table | Local spreadsheet/browser mock | Row reveal, cursor movement |
| 3. Prompt | 1:35-2:15 | Give the exact audit prompt | Local AI assistant mock | Typing |
| 4. AI Reasoning | 2:15-3:25 | Explain what AI should flag and why | AI result panel | Line-by-line reveal |
| 5. Negotiation | 3:25-4:35 | Turn findings into action | Call-script/checklist mock | Checklist reveal, cursor taps |
| 6. Savings | 4:35-5:20 | Make the value concrete | Proof card | Number pop, hold |
| 7. CTA | 5:20-5:45 | Drive comment/save action | CTA card | Subtle card motion |

## Caption Rules

- Burned captions use narration/source text only.
- Max 5 words per line.
- Captions never cover tables, dollar amounts, or CTA text.
- UI-only labels do not appear as subtitles.

## Approval Notes

This MVP intentionally uses local browser mocks and sample expenses. After script approval, the full render should use the same free/local visual pipeline and pyttsx3/local narration only.
