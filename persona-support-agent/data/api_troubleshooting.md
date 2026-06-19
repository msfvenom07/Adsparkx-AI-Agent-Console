# API Authentication and Troubleshooting Guide

This document outlines key configurations, header parameters, and error responses for integrating with the Adsparkx AI API.

## Authentication Mechanism

All Adsparkx AI API requests must be authenticated using a Bearer token. The API key must be placed in the `Authorization` header of each request:

```http
Authorization: Bearer sk_live_51Nx8X...
```

Do not include credentials in the URL query string. All API requests must use TLS 1.2 or higher.

## Request Headers

Each API request must include the following headers:
- `Authorization`: `Bearer <API_KEY>` (Required)
- `Content-Type`: `application/json` (Required for POST/PUT requests)
- `Adsparkx AI-Version`: `2026-04-01` (Recommended to lock API version)
- `Idempotency-Key`: `<UUID>` (Optional, to prevent duplicate requests)

## Error Status Codes

If an API request fails, Adsparkx AI returns a standard HTTP status code and a JSON response body:

- **400 Bad Request**: The request was unacceptable, often due to missing a required parameter.
- **401 Unauthorized**: No valid API key provided, or key is expired. Ensure the token is passed in the format `Bearer YOUR_KEY`.
- **403 Forbidden**: The API key does not have permissions to perform the requested operation.
- **404 Not Found**: The requested resource does not exist (e.g., incorrect customer_id).
- **429 Too Many Requests**: Too many requests hit the API too quickly. Rate limit exceeded.
- **500, 502, 503, 504 Internal Server Errors**: Something went wrong on Adsparkx AI's servers.

## Root Cause Analysis for 401 Unauthorized

1. **Missing 'Bearer' Prefix**: Make sure your Authorization header value is `Bearer sk_live_xxx` and not just `sk_live_xxx`.
2. **Whitespace Issues**: Ensure there is exactly one space between `Bearer` and the API key.
3. **Environment Mismatch**: Check that you are not using a sandbox/test API key in the production environment, or vice versa.
4. **API Key Revocation**: Verify in your dashboard that the API key has not been deleted or disabled.