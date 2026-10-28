# Helm Chart artifacts

Read for a Helm chart source. Apply the shared rules in [main skill](../SKILL.md), including archive inspection safeguards. For ambiguous registry sources, also read [container verification](container.md#verify-the-source) before selecting an artifact type.

## Verify the source

For Helm charts, verify the registry OCID and URL refer to the same chart version/digest. Inspect `Chart.yaml`, chart dependencies, and `kubeVersion` when accessible. Supply supported Kubernetes versions only from verified chart compatibility or publisher-provided testing information; distinguish declared compatibility from tested support. Do not infer chart version from `appVersion`. A local chart must be available through the registry source required by the live form; do not silently upload/push it elsewhere.

## Fill the artifact form

Choose the verified chart registry source. Use the established chart version/digest and Kubernetes compatibility evidence from verification; do not repeat identical reads merely to fill the form.
