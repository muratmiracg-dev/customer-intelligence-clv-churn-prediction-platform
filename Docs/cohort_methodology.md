# Cohort Retention Methodology

## Cohort Definition

A customer belongs to the calendar month of their first completed purchase.

## Cohort Index

- M0: first-purchase month;
- M1: one month after acquisition;
- …
- M12: twelve months after acquisition.

## Retention Rate

For cohort \(c\) and month index \(m\):

\[
\text{Retention}_{c,m} =
\frac{\text{Customers from cohort }c\text{ active in }m}
{\text{Customers acquired in cohort }c}
\]

## Interpretation

- Compare cohorts horizontally to observe decay after acquisition.
- Compare the same month index vertically to evaluate acquisition quality over time.
- Treat incomplete recent cohorts as right-censored.
- Investigate retention changes with acquisition channel, onboarding and promotional context.

## Limitation

Purchase-based retention may understate relationship continuity for customers with naturally long repurchase cycles.

