# Remote MCP example

Run `npm ci`, then `npm test` for local HTTP checks. Set `MCP_PUBLIC_KEY` to an RS256 public key, `MCP_ALLOWED_HOSTS` to your service hostname, and run `npm start`. Keep the private signing key with the token issuer. Clients send bearer JWTs with issuer and audience `mcp-example` and an expiration claim.

This example uses the maintained v1 TypeScript SDK and Streamable HTTP in stateless mode. It exposes one arithmetic tool. It does not implement OAuth discovery, browser access, or an identity provider. A client must support a configured bearer token. Choose an OAuth integration for clients that require interactive login.

Source: https://ts.sdk.modelcontextprotocol.io/server
