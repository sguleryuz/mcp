# Compute Image artifacts

Read for a Compute custom image source. Apply the shared authorization, context, archive, duplicate, readiness, and retention rules in [main skill](../SKILL.md).

## Verify the source

Apply the main skill's `phx`/`iad` source OCID check first. Verify Phoenix images in `us-phoenix-1` and Ashburn images in `us-ashburn-1`; keep the artifact destination in Ashburn without asking for a region.

For Compute images, inspect OS/version, launch options, and compatible shapes when exposed. Report architecture only with authoritative evidence. Confirm eligibility as a custom image; a platform or Marketplace image is not automatically a publishable source.

An already configured OCI CLI can retrieve read-only metadata with `oci compute image get`; check command help and region as directed by the main skill.

## Fill the artifact form

Confirm the exact source image OCID and its verified Phoenix or Ashburn region, and keep the artifact destination set to `us-ashburn-1`. Confirm that the live form accepts the source; do not replace a Phoenix source with an Ashburn image implicitly. Supply username, shape compatibility, and snapshot settings only from publisher instructions or verified metadata.
