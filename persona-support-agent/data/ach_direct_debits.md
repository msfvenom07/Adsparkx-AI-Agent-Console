# ACH Direct Debits and Return Codes

ACH payments allow US customers to pay directly using their checking or savings accounts.

## Verification and Mandates

Before pulling funds from a customer's account, you must obtain a signed billing authorization mandate. Bank accounts must be verified using micro-deposits (1-2 business days) or instant verification via Plaid.

## ACH Return Codes

Unlike credit cards, ACH transactions can fail days after they are initiated. Common return codes include:
- **R01 Insufficient Funds**: Customer did not have enough money in their account. Retrying is permitted.
- **R03 No Account / Unable to Locate**: Incorrect account number or routing transit number. Do not retry.
- **R20 Non-Transaction Account**: Account does not allow ACH withdrawals (e.g., some savings accounts).