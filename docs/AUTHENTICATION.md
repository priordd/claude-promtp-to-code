# Payment Service Authentication Guide

Complete guide for creating and using authentication tokens for testing the Payment Service API.

## 🔐 Overview

The Payment Service uses Bearer token authentication for API access. Currently, the service accepts any token that:
- Is in the format `Bearer <token>`
- Has a token part longer than 10 characters
- Is provided in the `Authorization` header

## 🚀 Quick Start

### 1. Generate Test Tokens
```bash
# Generate a complete set of test tokens
make generate-auth-tokens

# Or generate a simple token
make generate-auth-simple
```

### 2. Test Authentication
```bash
# Test with generated token
make test-auth

# Show curl examples
make curl-examples
```

### 3. Use in API Calls
```bash
# Example payment request (replace with actual token)
curl -X POST http://localhost:8000/api/v1/payments/process \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test_token_abc123defg456hij" \
  -d '{
    "merchant_id": "merchant_123",
    "amount": 99.99,
    "currency": "USD",
    "payment_method": "credit_card",
    "card_data": {
      "card_number": "4111111111111111",
      "expiry_month": 12,
      "expiry_year": 2025,
      "cvv": "123",
      "cardholder_name": "John Doe"
    },
    "description": "Test payment"
  }'
```

## 🛠️ Token Generation Methods

### Method 1: Using the Token Generator Script
```bash
# Generate all types of tokens
python scripts/generate_auth_tokens.py --save-env --curl-examples

# Generate specific token type
python scripts/generate_auth_tokens.py --type simple
python scripts/generate_auth_tokens.py --type uuid  
python scripts/generate_auth_tokens.py --type jwt
python scripts/generate_auth_tokens.py --type api_key

# Generate multiple tokens
python scripts/generate_auth_tokens.py --type simple --count 5
```

### Method 2: Using Makefile Commands
```bash
make generate-auth-tokens     # Complete set with examples
make generate-auth-simple     # Simple random token
make generate-auth-jwt        # JWT-like token
make test-auth               # Test generated token
make curl-examples           # Show usage examples
```

### Method 3: Manual Token Creation
```python
# Python example
import secrets
import string

def generate_token():
    alphabet = string.ascii_letters + string.digits
    token = ''.join(secrets.choice(alphabet) for _ in range(32))
    return f"Bearer test_token_{token}"

token = generate_token()
print(token)  # Bearer test_token_abc123...
```

```bash
# Bash one-liner
echo "Bearer test_token_$(openssl rand -hex 16)"
```

## 📋 Token Types and Examples

### 1. Simple Random Token
```
Bearer test_token_UKSZyHH7EkwD7skZOi2IGBBpjT9a046Q
```
- **Use case**: General testing
- **Length**: 43 characters
- **Pattern**: `Bearer test_token_<random_string>`

### 2. UUID-Based Token
```
Bearer uuid_a1522f7377754475bbd461f991db8de3
```
- **Use case**: Unique session identification
- **Length**: 37 characters  
- **Pattern**: `Bearer uuid_<uuid_hex>`

### 3. JWT-Like Token
```
Bearer eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJ1c2VyX2lkIjogInRlc3RfdXNlciIsICJtZXJjaGFudF9pZCI6ICJtZXJjaGFudF8xMjMiLCAic3ViIjogInRlc3RfdXNlciIsICJpYXQiOiAxNzUwNDYzODA1LCAiZXhwIjogMTc1MDU1MDIwNSwgImlzcyI6ICJwYXltZW50LXNlcnZpY2UiLCAiYXVkIjogInBheW1lbnQtYXBpIiwgInNjb3BlIjogWyJwYXltZW50OnByb2Nlc3MiLCAicGF5bWVudDpyZWZ1bmQiLCAicGF5bWVudDpyZWFkIl19.usQq5NQyKJNpW62Wt6wYA7uxtt5WnvF8wTpTASykO80
```
- **Use case**: JWT simulation (ready for future implementation)
- **Length**: 385 characters
- **Contains**: Header, payload, signature (base64 encoded)

### 4. API Key Style Token
```
Bearer test_merchant_123_82bf9d6d692da9c12ece1a37f8207b4e6b98f3d0
```
- **Use case**: Merchant-specific testing
- **Length**: 58 characters
- **Pattern**: `Bearer <env>_<merchant_id>_<random_hex>`

### 5. Minimal Valid Token
```
Bearer 1234567890
```
- **Use case**: Edge case testing (exactly 10 characters)
- **Length**: 10 characters (minimum allowed)

## ❌ Invalid Token Examples

### Tokens That Will Fail Authentication

```bash
# Too short (< 10 characters)
Bearer 123

# Empty token
Bearer 

# Missing Bearer prefix
just_a_token_without_bearer

# Malformed (no token part)
Bearer

# Wrong case
bearer test_token_123456789
BEARER TEST_TOKEN_123456789
```

## 🔧 Using Tokens in Different Contexts

### 1. Curl Commands
```bash
# GET request
curl -H "Authorization: Bearer <your_token>" \
     http://localhost:8000/api/v1/payments/<transaction_id>

# POST request with JSON body
curl -X POST \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <your_token>" \
     -d '{"merchant_id": "test"}' \
     http://localhost:8000/api/v1/payments/process
```

### 2. Python Requests
```python
import requests

headers = {
    "Authorization": "Bearer test_token_abc123defg456hij",
    "Content-Type": "application/json"
}

response = requests.post(
    "http://localhost:8000/api/v1/payments/process",
    headers=headers,
    json=payment_data
)
```

### 3. JavaScript/Fetch
```javascript
const headers = {
    'Authorization': 'Bearer test_token_abc123defg456hij',
    'Content-Type': 'application/json'
};

fetch('http://localhost:8000/api/v1/payments/process', {
    method: 'POST',
    headers: headers,
    body: JSON.stringify(paymentData)
});
```

### 4. Postman Collection
```json
{
    "auth": {
        "type": "bearer",
        "bearer": [
            {
                "key": "token",
                "value": "test_token_abc123defg456hij",
                "type": "string"
            }
        ]
    }
}
```

### 5. Load Testing (Locust)
Update `load-testing/.env`:
```bash
AUTH_TOKEN=Bearer test_token_abc123defg456hij
```

## 🚦 Testing Authentication

### 1. Test Valid Token
```bash
# Should return 200 with transaction data
curl -H "Authorization: Bearer test_token_abc123defg456hij" \
     http://localhost:8000/health
```

### 2. Test Invalid Token
```bash
# Should return 401 Unauthorized  
curl -H "Authorization: Bearer 123" \
     http://localhost:8000/api/v1/payments/process
```

### 3. Test Missing Token
```bash
# Should return 401 Unauthorized
curl http://localhost:8000/api/v1/payments/process
```

### 4. Automated Testing
```bash
# Run authentication tests
make test-auth

# Expected output for valid token:
# {
#   "status": "healthy",
#   "timestamp": "2025-06-20T...",
#   "version": "0.1.0",
#   "services": {...}
# }
```

## 📁 Environment Configuration

### 1. Generated Token File
After running `make generate-auth-tokens`, you'll get `test_tokens.env`:
```bash
# Test Authentication Tokens for Payment Service
AUTH_TOKEN=Bearer test_token_UKSZyHH7EkwD7skZOi2IGBBpjT9a046Q
AUTH_TOKEN_UUID=Bearer uuid_a1522f7377754475bbd461f991db8de3
AUTH_TOKEN_JWT_LIKE=Bearer eyJhbGciOiAiSFMyNTYi...
# ... more tokens
```

### 2. Load Into Environment
```bash
# Source the tokens
source test_tokens.env

# Use in curl
curl -H "Authorization: $AUTH_TOKEN" http://localhost:8000/health

# Or export specific token
export MY_TOKEN="Bearer test_token_abc123defg456hij"
```

### 3. Docker Environment
For Docker-based testing, add to your docker-compose.yml:
```yaml
environment:
  - AUTH_TOKEN=Bearer test_token_abc123defg456hij
```

## 🔍 Troubleshooting

### Common Issues

1. **401 Unauthorized**
   ```
   {"detail": "Authentication required"}
   ```
   - **Cause**: Missing Authorization header
   - **Fix**: Add `-H "Authorization: Bearer <token>"`

2. **401 Invalid Token**
   ```
   {"detail": "Invalid authentication token"}
   ```
   - **Cause**: Token too short (< 10 chars) or malformed
   - **Fix**: Use a token with >10 characters

3. **Token Not Working**
   - Check token format: Must start with "Bearer "
   - Verify token length: Must be >10 characters after "Bearer "
   - Check for extra spaces or special characters

### Debug Commands
```bash
# Check token format
echo "Bearer test_token_123456789" | wc -c  # Should be >16

# Test token validation
python -c "
token = 'Bearer test_token_123456789'
token_part = token[7:] if token.startswith('Bearer ') else ''
print(f'Valid: {len(token_part) >= 10}')
"

# Test API with verbose output
curl -v -H "Authorization: Bearer test_token_123456789" \
     http://localhost:8000/health
```

## 🔮 Future Authentication Features

The current implementation is designed to be easily upgradeable to:

1. **JWT Validation**: Real JWT signature verification
2. **Role-Based Access**: Different permissions per token
3. **Token Expiration**: Time-based token validity
4. **API Key Management**: Merchant-specific API keys
5. **OAuth2 Integration**: Standard OAuth2 flows

The JWT-like tokens generated by the script are already structured for easy migration to a full JWT implementation.

## 📚 API Endpoints Requiring Authentication

### Protected Endpoints
- `POST /api/v1/payments/process` - Process payment
- `GET /api/v1/payments/{transaction_id}` - Get payment status
- `POST /api/v1/payments/{transaction_id}/refund` - Process refund
- `GET /api/v1/merchants/{merchant_id}/transactions` - Get merchant transactions

### Public Endpoints
- `GET /health` - Health check (no auth required)
- `GET /` - Root endpoint (no auth required)

## 🎯 Best Practices

1. **Use Environment Variables**: Don't hardcode tokens in scripts
2. **Rotate Tokens**: Generate new tokens for different test sessions
3. **Test Both Valid and Invalid**: Include negative test cases
4. **Use Appropriate Length**: Tokens should be sufficiently long for security
5. **Document Token Usage**: Keep track of which tokens are for which purpose

This authentication system provides a solid foundation for testing while being ready for production-grade security enhancements.