# Webhook Configuration and Verification

Webhooks allow your application to receive real-time notifications about events in your Adsparkx AI account.

## How Webhooks Work

When an event occurs (e.g., a payment succeeds, a subscription is cancelled), Adsparkx AI generates an Event object and POSTs it as a JSON payload to your configured webhook URL.

## Webhook Signature Verification

To secure your webhook endpoint, verify that incoming requests are sent by Adsparkx AI. Adsparkx AI signs each webhook event payload and includes the signature in the header:

`X-Adsparkx AI-Signature: t=1672531199,v1=g83hf8h4...`

### Verification Steps:
1. Extract the timestamp `t` and signature `v1` from the `X-Adsparkx AI-Signature` header.
2. Create a HMAC-SHA256 signature using your endpoint's signing secret (whsec_...), the timestamp `t`, and the raw request payload concatenated as `timestamp.payload`.
3. Compare the computed signature with the extracted signature `v1` using a constant-time comparison helper to prevent timing attacks.
4. Check if the timestamp is within 5 minutes of the current time to prevent replay attacks.

## Troubleshooting Webhook Failures

- **HTTP 500/502/503/504 Errors**: Ensure your server responds with a 2xx HTTP code within 10 seconds. Adsparkx AI retries failed deliveries up to 16 times over 3 days using exponential backoff.
- **Signature Verification Fails**: Confirm that you are using the correct signing secret (whsec_...) for the active environment (test vs live) and that you are verifying the raw request body string, not a parsed JSON object.