# 09. RISK AND NO-BET SPECIFICATION

## Risk Engine Rules
1. If data validation indicates missing core inputs (e.g., player news unavailable), emit `NO_BET`.
2. If evidence conflict index > threshold, emit `NO_BET`.
3. If source reliability average < minimum required reliability, emit `NO_BET`.
4. If calculated probability edge or certainty is below minimum threshold, emit `NO_BET`.
