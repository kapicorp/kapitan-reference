# Terraform / OpenTofu JSON from Kapitan

This example shows Kapitan generating Terraform JSON (`*.tf.json`) for more than
one environment from a single Jsonnet template plus per-environment inventory.

Terraform and OpenTofu both read `*.tf.json` natively, so the compiled output is
ready to `plan`/`apply` without any extra conversion step. Kapitan generates the
configuration; Terraform or OpenTofu executes it.

Tested with Kapitan `0.36.1`.

## Layout

```
terraform-json/
  .kapitan                                  # pins the Kapitan version
  inventory/
    classes/
      common.yml                            # shared defaults
      terraform/network.yml                 # network params + compile config
    targets/
      dev.yml                               # dev overrides (CIDR, zones)
      prod.yml                              # prod overrides (region, CIDR, zones)
  components/
    terraform/network.tf.jsonnet            # the template that emits network.tf.json
  compiled/
    dev/terraform/network.tf.json
    prod/terraform/network.tf.json
```

## Run it

From this directory:

```bash
kapitan compile
```

Or, without a local install, using the Docker image:

```bash
docker run --rm -i -u "$(id -u)" --network host -w /src -v "$PWD:/src" \
  kapicorp/kapitan:0.36.1 compile
```

Each target writes `compiled/<target>/terraform/network.tf.json`. The two
environments differ only in their inventory: `dev` carves subnets from
`10.10.0.0/16` across two zones, `prod` uses `10.20.0.0/16` across three.

## Validate the output

```bash
cd compiled/dev/terraform
terraform init -backend=false
terraform validate
```

## A note on the resources

The template emits `terraform_data` resources, which are built into Terraform,
so the output validates without configuring a cloud provider or credentials.
For real infrastructure, replace `terraform_data` with provider resources such
as `google_compute_subnetwork` or `aws_subnet` and keep the same inventory split
between environments.

## Where Kapitan ends

Kapitan owns the inventory and the template, and produces the `*.tf.json` files.
From there Terraform or OpenTofu owns state, planning, and apply. The compiled
JSON can be committed for review or handed straight to a CI job.
