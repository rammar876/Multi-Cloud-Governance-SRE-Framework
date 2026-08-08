# Multi-Cloud Governance & SRE Framework

A provider-neutral governance model and executable reference implementation for consistent controls, policy-drift detection, and reliability management across AWS, Azure, and Google Cloud.

The framework separates **intent** from provider implementation. Teams define a control once, map it to native cloud services, normalize observations, and evaluate every environment with the same scoring and remediation workflow.

![Multi-cloud FinTech architecture overview](architecture/Multi-cloud%20FinTech%20architecture%20overview.png)

## Why this framework

AWS Config, Azure Policy, and Google Cloud controls are effective inside their own ecosystems, but their policy languages, evidence, and reporting models differ. This project supplies a common layer for:

- governance intent and cross-cloud control mapping;
- SLO, SLI, and error-budget integration;
- continuous configuration-drift detection;
- severity-weighted compliance reporting;
- remediation guidance with provider-native policy references;
- consistent security, reliability, observability, and FinOps evidence.

## Framework architecture

```text
Governance intent and risk requirements
                  │
        Normalized control catalog
          ┌───────┼────────┐
          │       │        │
      AWS Config  Azure    GCP controls
          │       Policy      │
          └───────┼───────────┘
                  │
       Normalized observations
                  │
       Drift and SRE evaluation
                  │
   Scorecard → remediation → evidence
```

The included evaluator is deliberately provider-neutral. Production collectors can transform AWS Config findings, Azure Policy states, and Google Cloud asset or security findings into the observation contract shown in `examples/`.

## Quick start

Python 3.10 or newer is required. The evaluator itself has no runtime dependencies.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .

mcgsre \
  --catalog policies/baseline.json \
  --observations examples/fintech-observations.json \
  --output report.json
```

Run directly from a checkout without installation:

```bash
PYTHONPATH=src python -m mcgsre \
  --catalog policies/baseline.json \
  --observations examples/fintech-observations.json
```

Use `--fail-on-drift` in CI. The command returns `0` when evaluation succeeds without enforced drift, `1` for invalid input, and `2` when drift is found with that option enabled.

## Data contracts

A normalized control declares expected state and provider mappings:

```json
{
  "id": "MCG-SEC-001",
  "title": "Storage encryption at rest",
  "severity": "critical",
  "expected": { "operator": "eq", "value": true },
  "provider_mappings": {
    "aws": "AWS Config rule",
    "azure": "Azure Policy definition",
    "gcp": "Security Health Analytics detector"
  },
  "remediation": "Enable encryption for the storage resource."
}
```

Collectors produce simple observations:

```json
{
  "provider": "aws",
  "resource_id": "arn:aws:s3:::payments-ledger",
  "control_id": "MCG-SEC-001",
  "actual": true
}
```

Supported comparison operators are `eq`, `gte`, `lte`, and `contains`. Scores are weighted by severity (`low=1`, `medium=2`, `high=3`, `critical=4`) so high-risk drift has proportionally greater impact.

## Repository contents

| Path | Purpose |
| --- | --- |
| `src/mcgsre/` | Validation, drift engine, report generation, and CLI |
| `policies/baseline.json` | Cross-cloud security, reliability, observability, and FinOps controls |
| `examples/fintech-observations.json` | Runnable multi-cloud sample evidence |
| `tests/` | Unit tests for evaluation and input validation |
| `case-study/fintech-use-case.md` | FinTech application and expected outcomes |
| `architecture/` | Framework architecture visual |

## Test and extend

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

To add a control, extend `policies/baseline.json`, map the intent to each applicable provider, and add representative compliant and drifted observations to the test suite. Cloud collectors should remain separate adapters so credentials and provider SDKs are not coupled to the evaluation engine.

## Operational adoption

1. Inventory workloads, owners, criticality, and regulatory scope.
2. Approve normalized controls and provider mappings through the governance body.
3. Deploy read-only evidence collectors in each cloud account, subscription, or project.
4. Evaluate on a schedule and on infrastructure changes; retain the JSON report as evidence.
5. Route critical drift to incident management and lower-severity drift to remediation backlogs.
6. Review SLOs and error-budget burn alongside compliance posture before approving releases.

## Research and case study

The framework accompanies *A Standardized Multi-Cloud Governance Model for Policy Consistency and Drift Detection* (May 4, 2026):

- [SSRN abstract 6713338](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6713338)
- [DOI 10.2139/ssrn.6713338](https://dx.doi.org/10.2139/ssrn.6713338)
- Conference submission: CloudCom 2026
- [FinTech use case](case-study/fintech-use-case.md)

Case-study performance figures are research targets or reported outcomes, not guarantees. Validate them against your own telemetry and audit requirements.

## Security and limitations

This repository is a reference implementation, not a replacement for provider enforcement, independent audit, or organization-specific risk assessment. Do not place credentials or sensitive cloud evidence in catalogs, observations, or generated reports. Collectors should use least-privilege read access, redact sensitive values, and protect retained evidence.

## License and citation

Copyright Ramesh Marella. All rights reserved; reuse requires permission. The associated paper is available under the terms stated by SSRN.

Suggested citation: Marella, Ramesh, *A Standardized Multi-Cloud Governance Model for Policy Consistency and Drift Detection* (May 4, 2026), DOI [10.2139/ssrn.6713338](https://dx.doi.org/10.2139/ssrn.6713338).

Contributions, implementation feedback, and provider-adapter proposals are welcome through GitHub issues and pull requests.
