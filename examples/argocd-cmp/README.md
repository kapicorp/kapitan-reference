# Argo CD Config Management Plugin for Kapitan

This example shows Argo CD rendering an application through a Config Management
Plugin (CMP) that runs Kapitan. Argo CD compiles the Kapitan target on the
repo-server side and applies the manifests Kapitan prints; there is no committed
rendered output for Argo CD to read.

Tested with Kapitan `0.36.1`.

## Layout

```
argocd-cmp/
  .kapitan
  cmp-plugin.yaml                   # ConfigManagementPlugin definition
  application.yaml                  # Argo CD Application using the plugin
  inventory/
    classes/common.yml
    targets/echo.yml
  components/
    manifests/app.jsonnet           # emits a Deployment and a Service
  compiled/
    echo/manifests/{deployment.yaml,service.yaml}
```

The `compiled/` directory is included so the example can be read and validated
on its own. In the Argo CD flow it is regenerated on the repo-server.

## What Argo CD runs

The plugin (`cmp-plugin.yaml`) reacts to any path containing a `.kapitan` file
and runs two steps. Argo CD exposes plugin env vars with an `ARGOCD_ENV_` prefix:

```yaml
init:
  command: [sh, -c]
  args: ["kapitan compile --targets \"$ARGOCD_ENV_KAPITAN_TARGET\""]
generate:
  command: [sh, -c]
  args: ["cat compiled/\"$ARGOCD_ENV_KAPITAN_TARGET\"/manifests/*.yaml"]
```

`generate` must print manifests to stdout. Argo CD applies whatever it reads.

## Try the plugin commands locally

This is exactly what the plugin does on the repo-server:

```bash
# init
docker run --rm -i -u "$(id -u)" --network host -w /src -v "$PWD:/src" \
  kapicorp/kapitan:0.36.1 compile --targets echo

# generate
cat compiled/echo/manifests/*.yaml
```

Validate the result with kubeconform:

```bash
docker run --rm -v "$PWD:/src" -w /src --entrypoint /kubeconform \
  ghcr.io/yannh/kubeconform:v0.6.7-alpine -summary -strict compiled/
# Summary: 2 resources found in 2 files - Valid: 2, Invalid: 0, Errors: 0, Skipped: 0
```

## Wiring it into Argo CD

1. Build a sidecar image that contains both the Kapitan binary and the
   `argocd-cmp-server` binary (copy `/var/run/argocd/argocd-cmp-server` from the
   Argo CD image into an image based on `kapicorp/kapitan:0.36.1`).
2. Add that image as a sidecar on `argocd-repo-server` and mount
   `cmp-plugin.yaml` at `/home/argocd/cmp-server/config/plugin.yaml`.
3. Apply `application.yaml`, pointing `repoURL` at your fork and `KAPITAN_TARGET`
   at the target you want.

## Out of scope

Installing Argo CD, building and pushing the sidecar image, and cluster access
are out of scope here. This example covers the plugin contract and the Kapitan
project it drives. The current Argo CD CMP sidecar pattern is assumed; check the
Argo CD docs for your version.
