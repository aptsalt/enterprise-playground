# Ideal Generate Test Prompts

5 prompts that exercise the full pipeline (routing, RAG, generation, caching) across all workflow categories.

## 1. Accounts — Checking Account Opening Flow
```
Create a TD checking account opening flow with eligibility check, document upload, and confirmation steps
```

## 2. Credit Cards — Comparison Dashboard
```
Build a credit card comparison dashboard showing rewards, APR, annual fees, and an apply now CTA for each card
```

## 3. Mortgages — Affordability Calculator
```
Generate a mortgage affordability calculator with income inputs, amortization schedule, and monthly payment breakdown
```

## 4. Personal Loans — Application Wizard
```
Design a personal loan application wizard with income verification, loan amount slider, rate preview, and submission review
```

## 5. Investing — Portfolio Overview
```
Build an investment portfolio overview with asset allocation pie chart, account balances, recent transactions table, and rebalance button
```

## Why These Work
- Each maps to a different **workflow category** so RAG pulls distinct chunks
- Specific enough for the **router** to confidently classify as `generate`
- Complex enough to produce **meaningful Agent traces** with visible latency across all 6 pipeline steps
- Running prompt #1 twice tests **cache hit** behavior on the Agent tab
