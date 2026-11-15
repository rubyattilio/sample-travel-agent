"""Let the offline tests import the agent without real keys (as in CI before secrets exist).

.env loads first, so local runs and RUN_JUDGE_TESTS=1 still use the real keys.
"""

import os

from dotenv import load_dotenv

load_dotenv()
for key in ("ANTHROPIC_API_KEY", "ARIZE_API_KEY", "ARIZE_SPACE_ID"):
    os.environ.setdefault(key, "placeholder-for-offline-tests")
