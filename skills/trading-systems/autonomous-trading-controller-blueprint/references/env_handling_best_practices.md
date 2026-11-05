# Environment Variable Handling Best Practices for ATC Blueprint

## .env File Management
- Never commit `.env` files to version control - they contain sensitive credentials
- Always provide a `.env.example` with placeholder values and clear comments
- When creating a new blueprint, check if `.env` already exists before overwriting
- If `.env` does not exist, create it from `.env.example` or prompt user to provide values
- Use environment variables for secrets like API tokens, account IDs, and private keys

## MetaAPI Credentials Specifics
- MetaAPI token should be treated as a secret - never expose in logs or code
- Account ID, while less sensitive, should still be protected
- Consider using a secrets manager or encrypted storage for production deployments
- For development/testing, .env file with proper permissions (600) is acceptable

## Validation
- After creating .env, verify it contains actual values (not placeholders) before running live trading
- Use a script to check for placeholder values and warn the user
- Example validation check:
  ```bash
  if grep -q "YOUR_META_API_TOKEN_PLACEHOLDER" .env; then
    echo "WARNING: MetaAPI token still contains placeholder value"
  fi
  ```

## Integration with ATC Components
- The MT5 adapter (`execution/mt5_adapter.py`) reads META_API_TOKEN and META_ACCOUNT_ID from environment
- Other components may need different environment variables (database URLs, API keys for other services)
- Document all required environment variables in README.md or a dedicated ENVIRONMENT.md file