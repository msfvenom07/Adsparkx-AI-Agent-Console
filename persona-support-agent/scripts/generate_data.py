import os
import sys
from pathlib import Path

# Ensure project root is in path
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Import directory configuration
from src.config import DATA_DIR

def generate_markdown_docs():
    """Generates the Markdown and Text support documents in the data folder."""
    
    docs = {
        "api_troubleshooting.md": (
            "# API Authentication and Troubleshooting Guide\n\n"
            "This document outlines key configurations, header parameters, and error responses "
            "for integrating with the Adsparkx AI API.\n\n"
            "## Authentication Mechanism\n\n"
            "All Adsparkx AI API requests must be authenticated using a Bearer token. "
            "The API key must be placed in the `Authorization` header of each request:\n\n"
            "```http\n"
            "Authorization: Bearer sk_live_51Nx8X...\n"
            "```\n\n"
            "Do not include credentials in the URL query string. All API requests must use TLS 1.2 or higher.\n\n"
            "## Request Headers\n\n"
            "Each API request must include the following headers:\n"
            "- `Authorization`: `Bearer <API_KEY>` (Required)\n"
            "- `Content-Type`: `application/json` (Required for POST/PUT requests)\n"
            "- `Adsparkx AI-Version`: `2026-04-01` (Recommended to lock API version)\n"
            "- `Idempotency-Key`: `<UUID>` (Optional, to prevent duplicate requests)\n\n"
            "## Error Status Codes\n\n"
            "If an API request fails, Adsparkx AI returns a standard HTTP status code and a JSON response body:\n\n"
            "- **400 Bad Request**: The request was unacceptable, often due to missing a required parameter.\n"
            "- **401 Unauthorized**: No valid API key provided, or key is expired. Ensure the token is passed in the format `Bearer YOUR_KEY`.\n"
            "- **403 Forbidden**: The API key does not have permissions to perform the requested operation.\n"
            "- **404 Not Found**: The requested resource does not exist (e.g., incorrect customer_id).\n"
            "- **429 Too Many Requests**: Too many requests hit the API too quickly. Rate limit exceeded.\n"
            "- **500, 502, 503, 504 Internal Server Errors**: Something went wrong on Adsparkx AI's servers.\n\n"
            "## Root Cause Analysis for 401 Unauthorized\n\n"
            "1. **Missing 'Bearer' Prefix**: Make sure your Authorization header value is `Bearer sk_live_xxx` and not just `sk_live_xxx`.\n"
            "2. **Whitespace Issues**: Ensure there is exactly one space between `Bearer` and the API key.\n"
            "3. **Environment Mismatch**: Check that you are not using a sandbox/test API key in the production environment, or vice versa.\n"
            "4. **API Key Revocation**: Verify in your dashboard that the API key has not been deleted or disabled."
        ),
        
        "billing_policy.txt": (
            "Adsparkx AI Billing and Invoicing Policy\n"
            "======================================\n\n"
            "This policy outlines payment terms, dispute resolution, refund conditions, and billing structures.\n\n"
            "1. Subscription Billing Cycle\n"
            "All SaaS subscriptions are billed in advance on a recurring monthly or annual schedule. "
            "Subscriptions automatically renew unless cancelled at least 24 hours prior to the next billing date. "
            "Proration is calculated automatically on upgrades or downgrades using a daily billing interval.\n\n"
            "2. Duplicate and Unexpected Charges\n"
            "If you detect duplicate charges on your bank statement:\n"
            "- Verify if another teammate authorized a separate seat/subscription.\n"
            "- Check if a recent retry of a failed transaction caused a temporary pending authorization hold. "
            "Holds typically drop off within 3-7 business days depending on your issuing bank.\n"
            "- If the charge is finalized, contact support with the transaction reference IDs (ch_xxxxxx) "
            "for a direct manual adjustment.\n\n"
            "3. Billing Disputes and Refunds\n"
            "All direct refund requests must be submitted within 30 days of the transaction date. "
            "Refunds are credited back to the original payment method only. "
            "Processing fees from the original transaction (2.9% + $0.30) are non-refundable.\n\n"
            "If a customer initiates a chargeback or payment dispute through their card issuer, a dispute fee "
            "of $15.00 is charged to the merchant account. The dispute process freezes the funds and takes 60-90 "
            "days to resolve via card association networks. Merchants must submit evidence such as signed invoices, "
            "tracking IDs, and user agreement logs to overturn chargebacks.\n\n"
            "4. Account Modifying Actions and Lockouts\n"
            "To modify credit card details, update subscription tiers, or cancel an account, administrators "
            "must log in to the Adsparkx AI dashboard. Support staff cannot perform account cancellations or transfer "
            "ownership over email or chat due to strict compliance standards."
        ),
        
        "webhook_configuration.md": (
            "# Webhook Configuration and Verification\n\n"
            "Webhooks allow your application to receive real-time notifications about events in your Adsparkx AI account.\n\n"
            "## How Webhooks Work\n\n"
            "When an event occurs (e.g., a payment succeeds, a subscription is cancelled), Adsparkx AI generates "
            "an Event object and POSTs it as a JSON payload to your configured webhook URL.\n\n"
            "## Webhook Signature Verification\n\n"
            "To secure your webhook endpoint, verify that incoming requests are sent by Adsparkx AI. "
            "Adsparkx AI signs each webhook event payload and includes the signature in the header:\n\n"
            "`X-Adsparkx AI-Signature: t=1672531199,v1=g83hf8h4...`\n\n"
            "### Verification Steps:\n"
            "1. Extract the timestamp `t` and signature `v1` from the `X-Adsparkx AI-Signature` header.\n"
            "2. Create a HMAC-SHA256 signature using your endpoint's signing secret (whsec_...), the timestamp `t`, "
            "and the raw request payload concatenated as `timestamp.payload`.\n"
            "3. Compare the computed signature with the extracted signature `v1` using a constant-time comparison helper "
            "to prevent timing attacks.\n"
            "4. Check if the timestamp is within 5 minutes of the current time to prevent replay attacks.\n\n"
            "## Troubleshooting Webhook Failures\n\n"
            "- **HTTP 500/502/503/504 Errors**: Ensure your server responds with a 2xx HTTP code within 10 seconds. "
            "Adsparkx AI retries failed deliveries up to 16 times over 3 days using exponential backoff.\n"
            "- **Signature Verification Fails**: Confirm that you are using the correct signing secret (whsec_...) "
            "for the active environment (test vs live) and that you are verifying the raw request body string, "
            "not a parsed JSON object."
        ),
        
        "payout_schedules.md": (
            "# Payout Schedules, Delays, and Currencies\n\n"
            "Adsparkx AI settles credit card and ACH funds directly to your linked business bank account.\n\n"
            "## Standard Payout Timelines\n\n"
            "- **US and Canada**: T+2 rolling basis (funds processed on Monday arrive on Wednesday).\n"
            "- **UK and Europe**: T+3 rolling basis.\n"
            "- **Australia and New Zealand**: T+4 rolling basis.\n"
            "- **ACH Direct Debits**: T+5 business days settlement time.\n\n"
            "## Reserve Balances and Holds\n\n"
            "Adsparkx AI may place a reserve hold on your account if you operate in a high-risk industry or experience "
            "elevated dispute rates. A reserve hold sets aside a percentage of your processing volume (usually 10%) "
            "for 90 days to cover potential chargebacks and refunds. If a payout is delayed, check the payouts "
            "tab in your dashboard to see if your account is subject to a reserve hold or bank verification delay.\n\n"
            "## Payout Currencies\n\n"
            "We support payouts in USD, EUR, GBP, AUD, CAD, JPY, and SGD. If you accept payments in a currency "
            "other than your bank's settlement currency, a 2.0% foreign exchange conversion markup is applied."
        ),
        
        "chargeback_disputes.md": (
            "# Chargeback Disputes and Evidence Submission\n\n"
            "A chargeback occurs when a cardholder disputes a transaction with their issuing bank.\n\n"
            "## The Dispute Lifecycle\n\n"
            "1. **Dispute Initiated**: The cardholder's bank reverses the payment. A dispute fee of $15.00 is debited "
            "from the merchant account along with the original transaction amount.\n"
            "2. **Evidence Submission**: The merchant has 15 days to submit evidence proving the transaction was valid.\n"
            "3. **Review**: The card network (Visa, Mastercard, etc.) reviews the case. This takes 60 to 90 days.\n"
            "4. **Resolution**: If resolved in your favor, the original amount is returned to your account. "
            "The $15.00 dispute fee is non-refundable regardless of the outcome.\n\n"
            "## Evidence Checklist\n\n"
            "To successfully dispute a chargeback, upload the following evidence via the dashboard:\n"
            "- Signed service agreement or customer contract.\n"
            "- IP addresses, log file entries, and timestamp records showing the user accessed the service.\n"
            "- Proof of delivery (tracking numbers for physical goods, download confirmation logs for digital assets).\n"
            "- Written customer communications demonstrating positive intent or acknowledgement of the charge."
        ),
        
        "refund_policy.md": (
            "# Customer Refund Policy and Transit Times\n\n"
            "This policy outlines guidelines for issuing, tracking, and completing customer refunds.\n\n"
            "## Issuing Refunds\n\n"
            "- Merchants can issue full or partial refunds directly via the dashboard or via the `/refunds` API endpoint.\n"
            "- Refunds can only be sent back to the original card or bank account used for the purchase. "
            "Under no circumstances should support personnel process refunds to an alternate card or PayPal account.\n"
            "- Original transaction fees (2.9% + $0.30) are not returned by credit card networks and are thus non-refundable.\n\n"
            "## Customer Refund Timelines\n\n"
            "- **Credit Cards**: Refunded amounts take 5 to 10 business days to appear on the customer's bank statement.\n"
            "- **ACH / Direct Debit**: ACH refunds can take up to 7 business days to process and clear back to the bank account."
        ),
        
        "pci_compliance_security.md": (
            "# PCI DSS Compliance and Tokenization\n\n"
            "The Payment Card Industry Data Security Standard (PCI DSS) regulates how cardholder data is stored and processed.\n\n"
            "## Tokenization and Adsparkx AI.js\n\n"
            "To reduce your security risk and simplify compliance, never send raw credit card numbers to your server. "
            "Instead, use Adsparkx AI.js or hosted payment fields. These libraries tokenize credit card data directly "
            "on the client's browser, returning a secure, single-use token (`tok_123456`) to your backend. "
            "This keeps your servers completely out of scope for complex PCI requirements.\n\n"
            "## Compliance Levels\n\n"
            "- **SAQ-A (Self-Assessment Questionnaire A)**: If you use hosted checkout or fully tokenized forms where "
            "cardholder data never touches your server. This requires minimal verification.\n"
            "- **SAQ-A-EP**: If you host your own forms but send card details to Adsparkx AI via browser-based scripts.\n"
            "- **SAQ-D**: If you handle, store, or transmit raw credit card details on your servers. This requires "
            "expensive quarterly audits, penetration testing, and firewall reviews."
        ),
        
        "enterprise_pricing.md": (
            "# Enterprise Pricing and Volume Discounts\n\n"
            "Adsparkx AI offers custom pricing structures for high-volume businesses and platforms.\n\n"
            "## Volume Tiers\n\n"
            "Our standard rate is 2.9% + $0.30 per transaction. Discounted pricing is available based on monthly volume:\n"
            "- **Level 1 ($0 - $50k / month)**: Standard pricing (2.9% + $0.30)\n"
            "- **Level 2 ($50k - $250k / month)**: Volume pricing (2.5% + $0.25)\n"
            "- **Level 3 ($250k - $1M / month)**: Custom Interchange-Plus model (typically cost + 0.4% + $0.15)\n"
            "- **Level 4 ($1M+ / month)**: Dedicated enterprise rates with custom contracts, dedicated account managers, "
            "and custom payouts.\n\n"
            "## Interchange-Plus Pricing\n\n"
            "Unlike fixed flat-rate pricing, Interchange-Plus charges the actual fee set by card associations (Visa, Mastercard) "
            "plus a transparent Adsparkx AI markup. This model is ideal for enterprises as it provides detailed transparency "
            "on card-brand fees."
        ),
        
        "multi_currency.md": (
            "# Multi-Currency Processing and Exchange Rates\n\n"
            "Adsparkx AI allows your business to charge customers in their local currency and settle in your home currency.\n\n"
            "## Supported Currencies\n\n"
            "We support processing in over 135 currencies. Settlement is supported in USD, EUR, GBP, AUD, CAD, JPY, and SGD.\n\n"
            "## Currency Conversion Markup\n\n"
            "When a payment requires currency conversion, Adsparkx AI applies a standard **2.0% markup fee** over the "
            "mid-market exchange rate. The rate is calculated at the exact timestamp of transaction authorization. "
            "Exchange rates are updated daily from leading financial data feeds."
        ),
        
        "ach_direct_debits.md": (
            "# ACH Direct Debits and Return Codes\n\n"
            "ACH payments allow US customers to pay directly using their checking or savings accounts.\n\n"
            "## Verification and Mandates\n\n"
            "Before pulling funds from a customer's account, you must obtain a signed billing authorization mandate. "
            "Bank accounts must be verified using micro-deposits (1-2 business days) or instant verification via Plaid.\n\n"
            "## ACH Return Codes\n\n"
            "Unlike credit cards, ACH transactions can fail days after they are initiated. Common return codes include:\n"
            "- **R01 Insufficient Funds**: Customer did not have enough money in their account. Retrying is permitted.\n"
            "- **R03 No Account / Unable to Locate**: Incorrect account number or routing transit number. Do not retry.\n"
            "- **R20 Non-Transaction Account**: Account does not allow ACH withdrawals (e.g., some savings accounts)."
        ),
        
        "rate_limiting.md": (
            "# API Rate Limiting and HTTP 429 Errors\n\n"
            "Adsparkx AI rate-limits API requests to ensure platform stability and protect resources.\n\n"
            "## Limit Thresholds\n\n"
            "- **Test Mode API Keys**: 100 requests per minute.\n"
            "- **Live Mode API Keys**: 100 requests per second (rps).\n"
            "- **Enterprise Keys**: Configurable up to 500 requests per second.\n\n"
            "## Rate Limit Headers\n\n"
            "Every response from Adsparkx AI includes standard rate-limiting headers:\n"
            "- `X-RateLimit-Limit`: Maximum requests permitted per second.\n"
            "- `X-RateLimit-Remaining`: Remaining request allowance in the current window.\n"
            "- `X-RateLimit-Reset`: Time remaining in seconds before the window resets.\n\n"
            "## Handling 429 Too Many Requests\n\n"
            "When limits are breached, the server returns an HTTP 429 error. Applications should catch this "
            "and retry using exponential backoff with jitter to prevent server thundering herd problems."
        ),
        
        "subscription_billing.md": (
            "# Subscription Billing, Duning, and Retries\n\n"
            "Adsparkx AI manages recurring customer billing automatically.\n\n"
            "## Billing States\n\n"
            "- **Active**: Subscription is paid and up-to-date.\n"
            "- **In Grace Period**: Payment failed, but service remains active while retries are attempted.\n"
            "- **Past Due**: Multiple payment attempts failed. Access to service should be suspended.\n"
            "- **Cancelled**: The subscription has been terminated.\n\n"
            "## Smart Duning Engine\n\n"
            "When a payment fails (e.g., card expired, card declined), Adsparkx AI's dunning system retries the charge "
            "up to 4 times over a 3-week period: Day 1, Day 3, Day 7, and Day 14. Custom email notifications are "
            "automatically sent to the customer reminding them to update card details before their subscription is suspended."
        )
    }
    
    for filename, content in docs.items():
        filepath = DATA_DIR / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Generated {filepath}")

def generate_pdf_doc():
    """Generates the required password_reset_guide.pdf using ReportLab."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
    except ImportError:
        print("Error: reportlab library not found. Run pip install reportlab first.")
        sys.exit(1)
        
    pdf_path = DATA_DIR / "password_reset_guide.pdf"
    
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom colors
    primary_color = colors.HexColor("#1A365D")  # Dark Blue
    secondary_color = colors.HexColor("#2B6CB0") # Medium Blue
    
    # Custom styles
    title_style = ParagraphStyle(
        'PDFTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=primary_color,
        alignment=0, # Left-aligned
        spaceAfter=15
    )
    
    heading_style = ParagraphStyle(
        'PDFHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=secondary_color,
        spaceBefore=12,
        spaceAfter=8,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'PDFBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=14.5,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=8
    )
    
    bullet_style = ParagraphStyle(
        'PDFBullet',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )
    
    story = []
    
    # Title
    story.append(Paragraph("Adsparkx AI Support Guide: Account Security and Password Resets", title_style))
    story.append(Spacer(1, 10))
    
    # Section 1
    story.append(Paragraph("1. Password Security Standards", heading_style))
    story.append(Paragraph(
        "Adsparkx AI enforces strict industry-standard security measures on user accounts to prevent unauthorized access. "
        "Your new password must satisfy the following minimum requirements:",
        body_style
    ))
    story.append(Paragraph("&bull; At least 12 characters in length.", bullet_style))
    story.append(Paragraph("&bull; Include at least one uppercase letter (A-Z) and one lowercase letter (a-z).", bullet_style))
    story.append(Paragraph("&bull; Include at least one digit (0-9) and one special character (e.g., !, @, #, $, %, &).", bullet_style))
    story.append(Paragraph("&bull; Must not match any of your 5 previously used passwords.", bullet_style))
    story.append(Spacer(1, 10))
    
    # Section 2
    story.append(Paragraph("2. Standard Password Reset Workflow", heading_style))
    story.append(Paragraph(
        "To reset your password, please follow these step-by-step instructions:",
        body_style
    ))
    story.append(Paragraph("1. Navigate to the Adsparkx AI Login portal and click on the 'Forgot Password' link below the input fields.", bullet_style))
    story.append(Paragraph("2. Input your registered administrative email address. Click 'Send Reset Instructions'.", bullet_style))
    story.append(Paragraph("3. Check your inbox for an automated email with the subject line 'Adsparkx AI Password Reset Code'. "
                           "The link inside this email is valid for exactly 15 minutes for security reasons.", bullet_style))
    story.append(Paragraph("4. Click the link and enter a new password meeting the security criteria specified in Section 1.", bullet_style))
    story.append(Paragraph("5. Confirm the password reset by entering your Multi-Factor Authentication (MFA) code.", bullet_style))
    story.append(Spacer(1, 10))
    
    # Section 3
    story.append(Paragraph("3. Multi-Factor Authentication (MFA) Recovery", heading_style))
    story.append(Paragraph(
        "If you lose access to your primary MFA device (authenticator app or security key):\n"
        "You must locate the 16-character backup recovery codes generated during your initial account configuration. "
        "Enter one of these recovery codes in the MFA input screen to log in and update your security details.",
        body_style
    ))
    story.append(Paragraph(
        "If you do not have your backup recovery codes, a account verification review is required. "
        "Please contact security-verification@adsparkx_ai.com with your business identification data to verify ownership.",
        body_style
    ))
    story.append(Spacer(1, 10))
    
    # Section 4
    story.append(Paragraph("4. Account Lockouts and Suspicious Attempts", heading_style))
    story.append(Paragraph(
        "Adsparkx AI locks accounts temporarily after 5 consecutive failed login attempts or password reset attempts. "
        "A lockout lasts for exactly 30 minutes. Once the lockout duration expires, the account is automatically unlocked. "
        "For urgent overrides, your organization's primary account owner can manually unlock your profile "
        "via the dashboard's Teammates management panel.",
        body_style
    ))
    
    # Build the document
    doc.build(story)
    print(f"Generated {pdf_path}")

if __name__ == "__main__":
    generate_markdown_docs()
    generate_pdf_doc()
    print("All sample data documents successfully generated!")
