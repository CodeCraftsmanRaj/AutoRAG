# Product Knowledge Base

## Support and access

- Password reset: go to Account Settings, choose Reset Password, and follow the verification email.
- Critical incident SLA: acknowledge within 15 minutes and provide updates every 30 minutes.
- API rate limits: documented in the API Guide under Rate Limiting.
- SSO: SAML 2.0 is available on Business and Enterprise plans.
- MFA: enable it in Security Settings and enroll an authenticator app.
- New team member onboarding: invite the user, assign role-based access, and require MFA.

## Security and privacy

- Data at rest encryption: AES-256 with managed KMS keys.
- API key rotation: create a new key, update clients, verify traffic, then revoke the old key.
- Audit log retention: 365 days by default.
- Data deletion: submit a request from Privacy Settings or through Support.
- API auth methods: bearer tokens and scoped service keys.
- Security support: use the dedicated security email and support portal.

## Platform behavior

- Failed background jobs: exponential backoff with up to five retries.
- Default session timeout: 30 minutes of inactivity.
- Storage limit increase: upgrade the plan or contact Support.
- Quota exceeded: requests are throttled until reset or quota expansion.
- Webhooks: configurable in Integration Settings with retry support.
- Billing report export: available as CSV from the Billing Console.

## Infrastructure and operations

- Deployment regions: US-East, EU-West, and AP-Southeast.
- Disaster recovery: documented in the Operations Runbook.
- Backups: created daily and restoration is tested periodically.
- Status and incidents: available on the public status page.
- Private networking: available on Enterprise with VPC peering.
