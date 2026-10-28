# Container Image artifacts

Read for a container source or when distinguishing a registry image from a Helm chart. Apply the shared rules in [main skill](../SKILL.md); also read [Helm guidance](helm.md) when the kind is ambiguous.

## Verify the source

For container images, inspect the repository, digest/version, registry URL, and source compartment. Match by OCID and digest where available rather than a mutable tag alone. The OCID prefix alone cannot distinguish a container image from a registry-hosted Helm chart. Inspect manifest media types and chart metadata: Helm chart config commonly uses `application/vnd.cncf.helm.config.v1+json`; verify chart name/version and package content where accessible. Do not classify from a tag, `.tgz` suffix, or application name alone. If registry tooling does not expose enough evidence, ask for chart metadata or package access before selecting Container Image versus Helm Chart.

An already configured OCI CLI can retrieve read-only metadata with `oci artifacts container image get`; check command help and region as directed by the main skill. Request only manifest fields needed for classification or identity, expanding inspection if those fields leave ambiguity.

## Fill the artifact form

Browse the source compartment, select the exact verified registry image, and confirm the resulting registry URL and digest.
