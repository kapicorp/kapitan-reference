# Custom Images for the HelmChart

```yaml
# -------------------------------------------------
# Parameters
# -------------------------------------------------
parameters:
  argocd:
    # -------------------------------------------------
    # HELM VALUES
    # -------------------------------------------------
    helm_values:
      dex:
        image:
          repository: ghcr.io/dexidp/dex
          tag: "v2.30.0"
          imagePullPolicy: Always
      redis-ha:
        image:
          repository: redis
          tag: "6.2.4-alpine"
      haproxy:
        image:
          repository: my-registry.example.com/path/to//haproxy
          tag: "2.0.4"
```


# Kapitan Plugin Dockerfile

After building the below image, just add this here:

```yaml
parameters:
  argocd:

    # -------------------------------------------------
    # IMAGES
    # -------------------------------------------------
    tools:
      kapitan:
        image: kapitan/argocd
```
## Dockerfile
```Dockerfile
# Tools image for argoCD

# ArgoCD ships python3.9 by default
# so lets build for 3.9
FROM python:3.9 as builder

# Fetch the latest package lists
# httplib2 and grafanalib versions are hardcoded
# as kapitan deps require it for now
ENV PATH=${PATH}:/home/app/.local/bin

RUN pip3 install \
  --no-cache-dir \
  --upgrade \
  --no-warn-script-location \
    pip \
    pex \
  && pex \
    httplib2==0.19.1 \
    kapitan==0.30.0rc1 \
    grafanalib==0.5.12 \
    --python=python3 \
    -m kapitan \
    -o /tmp/kapitan.pex

# Copy binaries into slim image
FROM python:3.9-slim

COPY --from=builder /tmp/kapitan.pex /usr/local/bin/kapitan

USER root

RUN apt-get update \
  && apt-get install \
    --no-install-recommends \
    -y \
    git \
  && rm -rf /var/lib/apt/lists/*

USER app
WORKDIR /app
ENTRYPOINT []
CMD ["/bin/bash"]
```