# Campaign Decisioning Playbook

## Decision Order

1. Check marketing consent and suppression rules.
2. Evaluate risk probability and risk tier.
3. Evaluate recent gross margin and predicted CLV.
4. Apply RFM strategy.
5. Estimate treatment response and cost.
6. Calculate expected incremental margin and ROI.
7. Allocate budget within the portfolio cap.
8. Track outcomes through a controlled experiment.

Before decisioning starts, the pipeline fails closed when customer identifiers are null or
duplicated, consent is not binary, model percentiles or probabilities fall outside the finite
0-to-1 range, or the campaign budget is negative or non-finite. These controls prevent
many-to-many joins and malformed scores from silently duplicating contacts or distorting spend.

## Recommended Actions

| Action | Intended Customer | Typical Objective |
|---|---|---|
| VIP Experience | High value, low-to-moderate risk | Protect and deepen relationship |
| Retain & Reward | Valuable customer with rising risk | Prevent avoidable churn |
| Onboarding | New or promising customer | Build early habit and retention |
| Cross-Sell | Engaged customer with category whitespace | Expand value |
| Win-Back | Lapsed customer with positive economics | Reactivate selectively |
| Nurture | Low-frequency but potentially valuable customer | Develop engagement |
| Suppress | No consent, negative economics or ineligible | Avoid contact and spend |

## Economic Measures

\[
\text{Expected Incremental Margin}
=
\text{Expected Response Value}
-
\text{Treatment Cost}
\]

\[
\text{Expected ROI}
=
\frac{\text{Expected Incremental Margin}}
{\text{Treatment Cost}}
\]

## Experiment Design

Every operational campaign should include:

- randomized holdout where practical;
- pre-registered primary metric;
- contact and fatigue limits;
- incremental margin, not gross response alone;
- customer-experience and complaint monitoring;
- post-campaign model and segment analysis.
