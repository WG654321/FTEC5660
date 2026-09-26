# Validation record

Checked on 26 September 2026 using Windows PowerShell and Python 3.14.2.

## Final implementation

The verified code commit is `63528a78bd69750c0b924db49874242dbd0a0232`.
Only the two permitted function bodies in `hw1.py` differ from the starter.
An AST comparison against the original template verified the rest of the file.
The chain uses LangChain and the required `deepseek-v4-flash-vision-exp` model
identifier, thinking enabled, and an output budget of 16,384 tokens.

## Real API tests

The original working directory and a fresh local Git clone each ran:

```bash
python hw1.py --image-folder public_test
```

Both completed successfully and produced the following `results.csv` answers:

| Query | Response | Correctness |
| --- | --- | --- |
| How much money did I spend in total for these bills? | HK$1974.30 | correct |
| How much would I have had to pay without the discount? | HK$2348.20 | correct |

Every individual receipt also matched the public per-receipt ground truth:

| Receipt | Paid after rounding | Before discounts |
| --- | ---: | ---: |
| receipt1.jpg | 394.70 | 480.20 |
| receipt2.jpg | 316.10 | 392.20 |
| receipt3.jpg | 140.80 | 160.10 |
| receipt4.jpg | 514.00 | 590.80 |
| receipt5.jpg | 102.30 | 107.70 |
| receipt6.jpg | 190.80 | 221.20 |
| receipt7.jpg | 315.60 | 396.00 |

The fresh clone used a new virtual environment and installed dependencies
directly from `requirements.txt`. Its API key was supplied through a temporary
process environment variable; no `.env` was copied into the clone. The final
code, including explicit positive-sign parsing, was verified in this clone.

## Offline and repository checks

- `python -m unittest discover -s tests`: all seven tests passed, also in the
  fresh clone. Cases cover exact aggregation, discount signs, positive and
  negative rounding, omitted discounts, inconsistent totals, invalid amounts
  and persistent API failures.
- `python -m pip check`: no broken dependencies.
- `git diff --check`: passed.
- Independent code review identified rejection of explicit positive rounding
  such as `+0.02`; the failure was reproduced, fixed and tested.
- `.env` is ignored and absent from tracked files. Tracked text files were
  checked for API keys before publication.

Installed direct dependencies were `langchain-core 1.6.5`,
`langchain-deepseek 1.1.1`, and `python-dotenv 1.2.3`.

## Scope and limitations

These are public-set results, not an estimate of private-test accuracy. No
private receipts are available. Accounting checks detect inconsistent OCR but
cannot prove that a self-consistent extraction matches the image. Earlier
development runs exposed a similar-digit OCR error and output truncation;
thinking mode and a larger output budget addressed these in subsequent runs.
Network/API failures still require valid credentials, account credit and a
working service. Explicit error responses preserve CSV generation during
extraction failures but are not correct monetary answers.
