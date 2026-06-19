# PCI DSS Compliance and Tokenization

The Payment Card Industry Data Security Standard (PCI DSS) regulates how cardholder data is stored and processed.

## Tokenization and Adsparkx AI.js

To reduce your security risk and simplify compliance, never send raw credit card numbers to your server. Instead, use Adsparkx AI.js or hosted payment fields. These libraries tokenize credit card data directly on the client's browser, returning a secure, single-use token (`tok_123456`) to your backend. This keeps your servers completely out of scope for complex PCI requirements.

## Compliance Levels

- **SAQ-A (Self-Assessment Questionnaire A)**: If you use hosted checkout or fully tokenized forms where cardholder data never touches your server. This requires minimal verification.
- **SAQ-A-EP**: If you host your own forms but send card details to Adsparkx AI via browser-based scripts.
- **SAQ-D**: If you handle, store, or transmit raw credit card details on your servers. This requires expensive quarterly audits, penetration testing, and firewall reviews.