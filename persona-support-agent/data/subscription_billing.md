# Subscription Billing, Duning, and Retries

Adsparkx AI manages recurring customer billing automatically.

## Billing States

- **Active**: Subscription is paid and up-to-date.
- **In Grace Period**: Payment failed, but service remains active while retries are attempted.
- **Past Due**: Multiple payment attempts failed. Access to service should be suspended.
- **Cancelled**: The subscription has been terminated.

## Smart Duning Engine

When a payment fails (e.g., card expired, card declined), Adsparkx AI's dunning system retries the charge up to 4 times over a 3-week period: Day 1, Day 3, Day 7, and Day 14. Custom email notifications are automatically sent to the customer reminding them to update card details before their subscription is suspended.