# SW-ADR-014 — No Fargate, no load balancer, no NAT gateway - free tier only

| Field | Value |
|---|---|
| ADR | `SW-ADR-014` |
| Pack | `SPENDWISE_V1` |
| Type | INFRASTRUCTURE |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | CLIENT |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 S2.3` · `SRC-001 S11.4` · `SRC-001 E-1` · `SRC-002 §15` |

## Context

SRC-001 S2.3 specifies ECS Fargate behind a load balancer and S11.4 specifies Secrets Manager. All three bill. The client ruled that nothing paid may be used, this being a learning project on a free-tier account.

## Options considered

- A. Keep the written stack and accept roughly $27-30/month.
- B. Free tier only - substitute every billing component.

## Decision

**B. Nothing paid. This OVERRIDES the client's own written stack.**

## Consequences

- ECS Fargate -> ECS on EC2 (t2/t3.micro, 750h free for 12 months). Fargate has no meaningful free tier.
- Application Load Balancer -> NONE. The task publishes to a host port and is reached by the instance's public IP. An ALB is ~$16-18/month regardless of traffic.
- Secrets Manager -> SSM Parameter Store (Standard). Free, same ECS integration pattern, same skill.
- Private subnets + NAT -> public subnet with assignPublicIp enabled and a locked-down security group. A NAT gateway is ~$32/month, larger than everything else combined.
- Unchanged: ECR, RDS, S3, and the two IAM roles of SRC-001 S11.5.
- THE HOLE THIS LEAVES: no load balancer means no straightforward HTTPS, so the Secure cookie flag of SRC-001 S10.4 cannot be set in the deployed environment without a domain and a certificate. The deployed environment runs HTTP with Secure=false, driven by an environment variable, and is NEVER called production in any document. A login cookie over plain HTTP is a real weakness, recorded as one.
- All figures above are approximate and UNVERIFIED by the build session. Check the AWS pricing pages.

---

*Accepted decisions are immutable. A reversal happens by a new superseding record, never by editing
this file. Recorded while `CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
