# Runnable specs

These scripts demonstrate the evidence ledger on real local state. Run them
from the repo root; each writes an inspectable `.ledger.jsonl` file you can open
and read.

```bash
uv run python specs/demo_basic.py    # record actions, verify the chain
uv run python specs/demo_tamper.py   # prove tamper-evidence on a hand-edited file
```

`demo_tamper.py` is the important one: it writes a clean ledger, edits a record
directly in the file (simulating an attacker), and shows the verifier catching
it and naming the exact record. That is the whole value of the tool, shown
rather than asserted.