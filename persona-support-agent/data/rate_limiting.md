# API Rate Limiting and HTTP 429 Errors

Adsparkx AI rate-limits API requests to ensure platform stability and protect resources.

## Limit Thresholds

- **Test Mode API Keys**: 100 requests per minute.
- **Live Mode API Keys**: 100 requests per second (rps).
- **Enterprise Keys**: Configurable up to 500 requests per second.

## Rate Limit Headers

Every response from Adsparkx AI includes standard rate-limiting headers:
- `X-RateLimit-Limit`: Maximum requests permitted per second.
- `X-RateLimit-Remaining`: Remaining request allowance in the current window.
- `X-RateLimit-Reset`: Time remaining in seconds before the window resets.

## Handling 429 Too Many Requests

When limits are breached, the server returns an HTTP 429 error. Applications should catch this and retry using exponential backoff with jitter to prevent server thundering herd problems.