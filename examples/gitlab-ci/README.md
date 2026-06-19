# Kapitan in GitLab CI

This example runs Kapitan inside GitLab CI: one job compiles the project and
keeps `compiled/` as an artifact, a second job validates the generated
Kubernetes manifests with [kubeconform](https://github.com/yannh/kubeconform).

Tested with Kapitan `0.36.1`.

## Layout

```
gitlab-ci/
  .kapitan
  .gitlab-ci.yml                    # compile -> validate pipeline
  inventory/
    classes/common.yml
    targets/echo.yml                # one app target
  components/
    manifests/app.jsonnet           # emits a Deployment and a Service
  compiled/
    echo/manifests/{deployment.yaml,service.yaml}
```

## The pipeline

```yaml
stages:
  - compile
  - validate

compile:
  image:
    name: kapicorp/kapitan:0.36.1
    entrypoint: [""]
  script:
    - kapitan compile
  artifacts:
    paths:
      - compiled/

validate:
  needs: [compile]
  image:
    name: ghcr.io/yannh/kubeconform:v0.6.7-alpine
    entrypoint: [""]
  script:
    - /kubeconform -summary -strict compiled/
```

Both images set their own entrypoint, so `entrypoint: [""]` lets GitLab run the
`script` block through a shell. The image tags are pinned on purpose; do not use
`latest` for a pipeline you depend on.

## Run the same steps locally

```bash
# compile
docker run --rm -i -u "$(id -u)" --network host -w /src -v "$PWD:/src" \
  kapicorp/kapitan:0.36.1 compile

# validate
docker run --rm -v "$PWD:/src" -w /src --entrypoint /kubeconform \
  ghcr.io/yannh/kubeconform:v0.6.7-alpine -summary -strict compiled/
```

Expected validate output:

```
Summary: 2 resources found in 2 files - Valid: 2, Invalid: 0, Errors: 0, Skipped: 0
```

## Optional follow-up: dynamic child pipelines

GitLab can treat a generated file as a
[child pipeline](https://docs.gitlab.com/ci/pipelines/downstream_pipelines/).
Kapitan can render that child `.gitlab-ci.yml` the same way it renders manifests
here, then a `trigger` job runs it. That is a separate step and is not required
for the basic compile-and-validate flow above.
