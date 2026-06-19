# Helmfile rendered by Kapitan

This example uses Kapitan as the inventory and template layer for
[Helmfile](https://github.com/helmfile/helmfile). Kapitan renders `helmfile.yaml`
and the environment-specific `values.yaml`; Helmfile stays responsible for Helm
release orchestration (`helmfile apply`, `sync`, `diff`).

Tested with Kapitan `0.36.1` and Helmfile `1.x`.

## Layout

```
helmfile/
  .kapitan
  inventory/
    classes/
      common.yml
      helmfile/release.yml          # repositories, release, and values defaults
    targets/
      dev.yml                       # dev overrides (1 replica, no ingress)
      prod.yml                      # prod overrides (3 replicas, ingress on)
  components/
    helmfile/
      helmfile.yaml                 # Jinja2 template -> helmfile.yaml
      values.yaml                   # Jinja2 template -> values.yaml
  compiled/
    dev/helmfile/{helmfile.yaml,values.yaml}
    prod/helmfile/{helmfile.yaml,values.yaml}
```

## Run it

```bash
kapitan compile
```

Or via Docker:

```bash
docker run --rm -i -u "$(id -u)" --network host -w /src -v "$PWD:/src" \
  kapicorp/kapitan:0.36.1 compile
```

Both environments install the public `podinfo` chart. They differ only in their
inventory: `dev` runs one replica with ingress off, `prod` runs three with
ingress on.

## Hand it to Helmfile

```bash
cd compiled/prod/helmfile
helmfile build      # parse and print the resolved release set
helmfile diff       # compare against the cluster (needs a kubeconfig)
helmfile apply
```

## Division of responsibility

Kapitan owns the inventory and renders `helmfile.yaml` plus the per-environment
`values.yaml`. Helmfile reads those files and drives Helm to install, diff, and
upgrade releases. Kapitan does not replace Helmfile; it removes the copy-paste
between environments by generating the Helmfile state from one source of truth.
