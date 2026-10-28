# Terraform Stack artifacts

Read for a Resource Manager stack or supplied Terraform configuration. Apply the shared rules in [main skill](../SKILL.md), including archive inspection safeguards.

## Verify the source

For Terraform stacks, inspect the Resource Manager stack's OCID, region, compartment, lifecycle state, Terraform version, configuration source, and existing validation/job results when available. Validate eligibility using the current Publisher picker and guidelines; do not claim readiness from a stack OCID alone. Where the flow requires successful Apply/Destroy evidence, inspect existing jobs and report missing prerequisites. Creating an artifact does not authorize running those jobs.

For a supplied Terraform archive/configuration, inspect the package read-only for Terraform configuration and required files/layout. Do not confuse Terraform state/plan files, a Helm archive, or a repository URL with a publishable Terraform configuration package. Do not execute configuration or expose secrets/state in output. If the live Console supports configuration upload, use only its accepted format and validate the uploaded selection. If it requires a Resource Manager stack, request an existing eligible stack; creating that prerequisite requires a separate request. Resolve any Marketplace image listing IDs referenced by the stack from verified configuration or publisher inputs, as missing references can fail validation.

An already configured OCI CLI can retrieve read-only metadata with `oci resource-manager stack get`; check command help and region as directed by the main skill.

## Fill the artifact form

Select the verified Resource Manager stack, or upload the verified configuration only when the live form supports it. Include the verified referenced Marketplace image listing IDs when applicable. Use the accepted format and validate the resulting selection.
