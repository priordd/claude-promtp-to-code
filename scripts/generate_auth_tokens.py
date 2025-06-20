#!/usr/bin/env python3
"""
Authorization Token Generator for Payment Service Testing

This script generates various types of authentication tokens for testing
the Payment Service API endpoints.
"""

import secrets
import string
import uuid
import base64
import json
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import argparse

class TokenGenerator:
    """Generates different types of authentication tokens for testing."""
    
    def __init__(self, secret_key: str = "payment_service_secret_key_2024"):
        self.secret_key = secret_key
    
    def generate_simple_token(self, length: int = 32) -> str:
        """Generate a simple random token (current API requirement: >10 chars)."""
        alphabet = string.ascii_letters + string.digits
        token = ''.join(secrets.choice(alphabet) for _ in range(length))
        return f"test_token_{token}"
    
    def generate_uuid_token(self) -> str:
        """Generate UUID-based token."""
        return f"uuid_{uuid.uuid4().hex}"
    
    def generate_jwt_like_token(self, 
                               user_id: str = "test_user",
                               merchant_id: str = "merchant_123",
                               expires_in_hours: int = 24) -> str:
        """Generate a JWT-like token with payload (for future JWT implementation)."""
        # Header
        header = {
            "alg": "HS256",
            "typ": "JWT"
        }
        
        # Payload  
        now = datetime.utcnow()
        payload = {
            "user_id": user_id,
            "merchant_id": merchant_id,
            "sub": user_id,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=expires_in_hours)).timestamp()),
            "iss": "payment-service",
            "aud": "payment-api",
            "scope": ["payment:process", "payment:refund", "payment:read"]
        }
        
        # Encode (simplified - not a real JWT)
        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
        
        # Create signature
        message = f"{header_b64}.{payload_b64}".encode()
        signature = hmac.new(
            self.secret_key.encode(), 
            message, 
            hashlib.sha256
        ).digest()
        signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip('=')
        
        return f"{header_b64}.{payload_b64}.{signature_b64}"
    
    def generate_api_key_token(self, 
                              merchant_id: str = "merchant_123",
                              environment: str = "test") -> str:
        """Generate API key style token."""
        prefix = f"{environment}_{merchant_id}"
        random_part = secrets.token_hex(20)
        return f"{prefix}_{random_part}"
    
    def generate_bearer_token(self, token_type: str = "simple") -> str:
        """Generate bearer token with Bearer prefix."""
        if token_type == "simple":
            token = self.generate_simple_token()
        elif token_type == "uuid":
            token = self.generate_uuid_token()
        elif token_type == "jwt":
            token = self.generate_jwt_like_token()
        elif token_type == "api_key":
            token = self.generate_api_key_token()
        else:
            token = self.generate_simple_token()
        
        return f"Bearer {token}"
    
    def generate_test_tokens_set(self) -> Dict[str, Any]:
        """Generate a complete set of test tokens for different scenarios."""
        return {
            "valid_tokens": {
                "simple": self.generate_bearer_token("simple"),
                "uuid": self.generate_bearer_token("uuid"), 
                "jwt_like": self.generate_bearer_token("jwt"),
                "api_key": self.generate_bearer_token("api_key"),
                "long_token": f"Bearer {'x' * 100}",  # Very long token
                "minimal_valid": "Bearer 1234567890"  # Minimum length (10 chars)
            },
            "invalid_tokens": {
                "too_short": "Bearer 123",  # Less than 10 chars
                "empty": "Bearer ",
                "no_bearer": "just_a_token_without_bearer",
                "malformed": "Bearer",  # Just "Bearer" without token
                "null_token": None,
                "special_chars": "Bearer token@#$%^&*()",
            },
            "edge_cases": {
                "bearer_lowercase": "bearer test_token_123456789",
                "extra_spaces": "Bearer   test_token_123456789   ",
                "different_case": "BEARER TEST_TOKEN_123456789",
                "mixed_case": "BeArEr TeSt_ToKeN_123456789"
            }
        }

def print_token_info(token: str):
    """Print token information and validation status."""
    print(f"Token: {token}")
    print(f"Length: {len(token) if token else 0}")
    
    if token and token.startswith("Bearer "):
        token_part = token[7:]  # Remove "Bearer " prefix
        print(f"Token part: {token_part}")
        print(f"Token part length: {len(token_part)}")
        print(f"Valid (>10 chars): {len(token_part) >= 10}")
    else:
        print("Invalid format: Missing 'Bearer ' prefix")
    print("-" * 50)

def generate_curl_examples(tokens: Dict[str, Any]):
    """Generate curl command examples for testing."""
    print("\n🔧 CURL COMMAND EXAMPLES:")
    print("=" * 50)
    
    # Valid token example
    valid_token = tokens["valid_tokens"]["simple"]
    print("\n✅ Valid Payment Request:")
    print(f"""curl -X POST http://localhost:8000/api/v1/payments/process \\
  -H "Content-Type: application/json" \\
  -H "Authorization: {valid_token}" \\
  -d '{{
    "merchant_id": "merchant_123",
    "amount": 99.99,
    "currency": "USD",
    "payment_method": "credit_card",
    "card_data": {{
      "card_number": "4111111111111111",
      "expiry_month": 12,
      "expiry_year": 2025,
      "cvv": "123",
      "cardholder_name": "John Doe"
    }},
    "description": "Test payment"
  }}'""")
    
    print("\n✅ Health Check (no auth required):")
    print("curl -X GET http://localhost:8000/health")
    
    print("\n❌ Invalid Token Example:")
    print(f"""curl -X POST http://localhost:8000/api/v1/payments/process \\
  -H "Content-Type: application/json" \\
  -H "Authorization: {tokens['invalid_tokens']['too_short']}" \\
  -d '{{"merchant_id": "test"}}'""")

def generate_environment_file(tokens: Dict[str, Any]):
    """Generate .env file with test tokens."""
    env_content = f"""# Test Authentication Tokens for Payment Service
# Generated on {datetime.now().isoformat()}

# Primary test token (use this for most testing)
AUTH_TOKEN={tokens['valid_tokens']['simple']}

# Alternative valid tokens
AUTH_TOKEN_UUID={tokens['valid_tokens']['uuid']}
AUTH_TOKEN_JWT_LIKE={tokens['valid_tokens']['jwt_like']}
AUTH_TOKEN_API_KEY={tokens['valid_tokens']['api_key']}

# Minimal valid token
AUTH_TOKEN_MINIMAL={tokens['valid_tokens']['minimal_valid']}

# Invalid tokens (for negative testing)
AUTH_TOKEN_INVALID_SHORT={tokens['invalid_tokens']['too_short']}
AUTH_TOKEN_INVALID_EMPTY={tokens['invalid_tokens']['empty']}

# Load testing configuration
LOCUST_AUTH_TOKEN={tokens['valid_tokens']['simple']}
"""
    
    with open('test_tokens.env', 'w') as f:
        f.write(env_content)
    
    print(f"\n💾 Environment file saved: test_tokens.env")
    print("   Add to your .env file or source directly:")
    print("   source test_tokens.env")

def main():
    parser = argparse.ArgumentParser(description="Generate authentication tokens for Payment Service testing")
    parser.add_argument("--type", choices=["simple", "uuid", "jwt", "api_key", "all"], 
                       default="all", help="Type of token to generate")
    parser.add_argument("--count", type=int, default=1, help="Number of tokens to generate")
    parser.add_argument("--user-id", default="test_user", help="User ID for JWT-like tokens")
    parser.add_argument("--merchant-id", default="merchant_123", help="Merchant ID for tokens")
    parser.add_argument("--save-env", action="store_true", help="Save tokens to environment file")
    parser.add_argument("--curl-examples", action="store_true", help="Show curl command examples")
    
    args = parser.parse_args()
    
    generator = TokenGenerator()
    
    print("🔐 Payment Service Authentication Token Generator")
    print("=" * 60)
    
    if args.type == "all":
        # Generate complete token set
        tokens = generator.generate_test_tokens_set()
        
        print("\n✅ VALID TOKENS:")
        for name, token in tokens["valid_tokens"].items():
            print(f"\n{name.upper()}:")
            print_token_info(token)
        
        print("\n❌ INVALID TOKENS (for negative testing):")
        for name, token in tokens["invalid_tokens"].items():
            print(f"\n{name.upper()}:")
            print_token_info(token)
        
        print("\n🔍 EDGE CASES:")
        for name, token in tokens["edge_cases"].items():
            print(f"\n{name.upper()}:")
            print_token_info(token)
        
        if args.save_env:
            generate_environment_file(tokens)
        
        if args.curl_examples:
            generate_curl_examples(tokens)
            
    else:
        # Generate specific token type
        print(f"\nGenerating {args.count} {args.type.upper()} token(s):")
        for i in range(args.count):
            if args.type == "simple":
                token = generator.generate_bearer_token("simple")
            elif args.type == "uuid":
                token = generator.generate_bearer_token("uuid")
            elif args.type == "jwt":
                token = generator.generate_jwt_like_token(args.user_id, args.merchant_id)
            elif args.type == "api_key":
                token = generator.generate_api_key_token(args.merchant_id)
            
            print(f"\nToken {i+1}:")
            print_token_info(f"Bearer {token}" if args.type in ["jwt", "api_key"] else token)
    
    print("\n📝 USAGE NOTES:")
    print("• Current API accepts any token with >10 characters")
    print("• Use 'Bearer <token>' format in Authorization header")
    print("• For Locust testing, update load-testing/.env")
    print("• For curl testing, use -H 'Authorization: Bearer <token>'")
    print("• Health endpoint (/health) doesn't require authentication")

if __name__ == "__main__":
    main()