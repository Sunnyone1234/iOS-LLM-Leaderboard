# Natural Language Expense Extraction

## Scenario

A personal finance app lets users enter expenses in natural language.

## Prompt

Extract structured expense data from this sentence: "Lunch with Alex was 18.50 euros yesterday at Cafe Central." Return JSON with amount, currency, merchant, category, date reference, and participants.

## Expected Behavior

- Returns valid structured output.
- Identifies amount and currency.
- Extracts merchant and participant.
- Uses a reasonable category.
- Preserves uncertainty for relative dates.

## Scoring Rubric

Evaluate task accuracy, structured output quality, robustness, cost/latency awareness, and safety where relevant.

## Notes for Reviewers

Do not require a specific date resolution unless the evaluation environment defines one.
