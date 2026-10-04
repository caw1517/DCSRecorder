"""Acceptance signal over the retained live attempt; expected red until recapture."""
from pathlib import Path
import re
import sys

text = Path(sys.argv[1]).read_text(encoding='utf-8', errors='replace')
errors = re.findall(r'DCSGROUND,1,ERROR,[^\r\n]+', text)
stops = re.findall(r'DCSREC_LOG,1,END,\d+,invalid_sample,\d+', text)
rows = re.findall(r'DCSGROUND,1,DATA,[^\r\n]+', text)
if errors or stops or not rows:
    print('FAIL: automatic stop before a usable ground recording')
    for item in errors + stops:
        print(item)
    print('Paired contact rows:', len(rows))
    sys.exit(1)
print('PASS: ground rows present without the observed automatic-stop failure')
