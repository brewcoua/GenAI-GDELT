# 4. Results

This section reports findings for the three research questions: the volume of
generative-AI governance coverage over time (RQ1), the distribution and evolution of
frames (RQ2), and whether governance milestones coincide with shifts in coverage (RQ3).
All analyses draw on 273,631 English-language news articles indexed in the GDELT 2.0
Global Knowledge Graph between 1 November 2022 and 14 June 2026, identified through a
generative-AI keyword filter applied to article URLs (see §3). Frame classification was
performed with a transparent rule-based keyword dictionary; because the classifier
operates on headline text and a substantial share of headlines carry no detectable
governance frame, reported frame prevalences should be read as *lower bounds* rather than
exact proportions. Following the multi-label design (§3), an article may invoke more than
one frame, so frame prevalences sum to more than 100%.

---

## 4.1 RQ1 — Volume of coverage over time

Generative-AI news coverage grew dramatically following the launch of ChatGPT and did not
revert to its pre-launch baseline at any point in the study window. Monthly coverage rose
from 541 articles in November 2022 — the launch month — to a first peak of 9,891 in May
2023, an roughly eighteen-fold increase within six months. Rather than subsiding after the
initial period of intense novelty, coverage settled into a high but volatile plateau
through 2024 (typically 4,000–6,500 articles per month) before climbing again through 2025
and into 2026 to new sustained highs of roughly 9,000–11,000 articles per month. The
single highest month in the series was November 2023 (11,587 articles).

The governance-flagged subset — articles whose URL or GDELT theme tags indicate a
regulatory, legal, ethical, safety, or rights dimension — tracked the overall series
closely throughout, consistently representing approximately one third of total coverage.
Governance-oriented attention therefore scaled *with* overall attention from early in the
period rather than emerging later as a growing share; the salience of governance as a
dimension of AI coverage was established quickly and sustained.

Three features of the series warrant caution in interpretation. First, the final month
(June 2026) is partial, as data collection ended on 14 June, and its lower value should not
be read as a decline. Second, month-to-month volatility is high, reflecting both
event-driven coverage and the syndication of wire stories across many outlets; individual
months should not be over-interpreted, though the overall trend and the major peaks are
robust. Third, the largest peaks are confounded by co-occurring events — most notably the
November 2023 peak, which coincides with both the Bletchley Park AI Safety Summit and the
OpenAI leadership crisis, making single-cause attribution impossible.

*[Figure 1: Monthly coverage volume, all generative-AI coverage and governance-flagged
subset, Nov 2022 – Jun 2026.]*

---

## 4.2 RQ2 — Frame distribution and evolution

### What the frames capture

Before reporting magnitudes, we describe what each frame captures in this corpus, since
the substantive content of the framing is the primary object of interest. The **innovation**
frame is dominated by product-launch coverage (new models, features, and releases) and
secondarily by capability and productivity sub-themes. The **economic/competition** frame
is led by market and investment coverage (funding, valuations, deals) and by corporate and
geopolitical competition. The **regulation** frame is led by litigation and legal coverage
(lawsuits, court cases) and by government oversight and lawmaking. The **risk** frame divides
between security/cyber concerns (including, in the later period, military and defence
applications), existential and safety concerns, and harm to vulnerable groups. The
**rights/privacy** frame is led by copyright and intellectual-property disputes and by data
privacy. The **misinformation** frame — the smallest throughout — comprises deepfakes,
fabricated content, and election-related manipulation.

### Overall distribution

Across the full corpus, **innovation (15.5%)** and **economic/competition (15.3%)** were the
most prevalent frames, followed by **regulation (12.6%)**, **risk (10.2%)**,
**rights/privacy (3.8%)**, and **misinformation (1.5%)**. Generative AI was thus framed
predominantly through capability and market lenses, with governance-oriented framing
(regulation, risk, rights) present but secondary. This ordering is consistent with prior
AI-framing work: Chuan et al. (2019) found business/economy the dominant topic in AI news,
and Hendrickx & Van Coppenolle (2026) likewise found positively valenced "tool" framing
the most common single frame in quality-press GenAI coverage.

### Evolution over time

The frame mix was not static. Three trajectories are notable (Figure 2). First, the
**regulation** frame rose sharply in 2023 — from 3.3% in 2022Q4 to 16.4% in 2023Q2 — during
the period of intense early governance debate, then oscillated between roughly 7% and 13%
through 2024 and early 2025 before rising again to 17.1% in 2026Q1. Second, the **innovation**
frame, stable around 15–19% for the first three years, fell to its lowest observed value
(11.4%) in 2026Q1. Third, the **risk** frame, confined to a 4–8% band for most of the period,
broke sharply upward to 16.8% in 2025Q3 and 19.9% in 2026Q1, where it became the single most
prevalent frame, overtaking innovation. Taken together, these trajectories indicate a
broadening of coverage away from a purely technological/innovation framing toward
governance- and risk-oriented framing in the later period — a pattern directly echoing
Hendrickx & Van Coppenolle's (2026) observation that GenAI coverage broadened from
technological to regulatory and societal dimensions after ChatGPT's launch.

The 2026Q1 risk surge requires an important qualification. Inspection of the risk-flagged
articles in that quarter shows the increase is concentrated around a single high-salience
controversy — a dispute between the U.S. Department of Defense and the AI company Anthropic
— rather than reflecting a diffuse shift toward risk framing across all coverage. The risk
surge is therefore best understood as event-driven: a single governance-adjacent
controversy can dominate the risk frame for an entire quarter. (The earlier 2025Q3 risk
elevation was not separately inspected and may or may not be similarly event-concentrated;
this is noted as a limitation.)

*[Figure 2: Frame prevalence by quarter, Nov 2022 – early 2026.]*

---

## 4.3 RQ3 — Governance milestones and shifts in coverage

To assess whether governance milestones coincide with shifts in coverage, we defined a set
of governance milestones from external chronology — independent of where attention peaks
occur in our data, to avoid fitting milestones to spikes — and compared frame prevalence in
the three months before versus the three months after each. The milestones comprised the
March 2023 "Pause AI" open letter, the November 2023 Bletchley Park AI Safety Summit, the
December 2023 EU AI Act political agreement, the August 2024 entry into force of the EU AI
Act, the February 2025 prohibition-of-practices deadline, the August 2025 general-purpose AI
obligations deadline, and the November 2025 EU "AI omnibus" simplification.

The central finding is that governance milestones coincide with shifts in framing
**selectively**, depending on the nature of the milestone. The novel, contested,
agenda-setting events of 2023 were each followed by marked increases in the regulation
frame: +9.8 percentage points after the Pause-AI letter, +8.6pp after the Bletchley Summit,
and +7.8pp after the EU AI Act political agreement, typically accompanied by smaller
increases in the risk frame. By contrast, the routine *implementation* deadlines of
2024–early 2025 — the Act entering into force (August 2024) and the prohibited-practices
deadline (February 2025) — were followed by *no* increase, and in fact slight decreases, in
regulation framing (−2.7pp and −2.6pp respectively). The August 2025 general-purpose AI
deadline, which unlike the earlier procedural dates imposed concrete obligations on the
specific model providers that dominate coverage, was an exception, coinciding with a +5.6pp
rise in regulation framing.

This pattern suggests that news media frame AI governance as newsworthy when it is
politically contested and novel — summits, open letters, the first agreement on a major law
— rather than when it is administratively enacted through compliance deadlines. The
regulation-framing trajectory observed independently in RQ2 (the 2023 rise and subsequent
oscillation) corroborates this interpretation, providing two convergent views of the same
phenomenon.

Two caveats constrain these results. First, the analysis is strictly correlational: a frame
rising after a milestone does not establish that the milestone caused the shift, and several
milestones co-occur with unrelated high-salience events (most notably Bletchley with the
OpenAI leadership crisis). Second, the late-2023 milestones cluster temporally, so their
before/after windows overlap and the three large regulation increases reported above are not
statistically independent — they are better understood as a single sustained period of
elevated regulation framing than as three separate effects.

*[Figure 3: Coverage volume with governance milestones overlaid. Figure 4: per-milestone
before/after frame-prevalence table.]*

---

## 4.4 Summary of findings

Coverage of generative AI grew dramatically and durably after ChatGPT's launch (RQ1), with
governance-oriented coverage scaling proportionally throughout. Framing was dominated by
innovation and economic/competition lenses for most of the period, with a pronounced late
shift toward risk and regulation framing in 2025–2026, though the sharpest risk increase was
concentrated around a single controversy (RQ2). Governance milestones coincided with
increases in regulation framing selectively — around novel and contested events rather than
routine implementation deadlines (RQ3). Across all three questions, the relative patterns
and trajectories are the robust findings; absolute frame prevalences are lower bounds given
the keyword-based classification, and all milestone analyses are correlational.
