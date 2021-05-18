# Documentation for trivy on examples

|||
| --- | ---- |
| **Component name** | trivy |
| **Application** | Not Defined |
| **Replicas** | 1 |
| **Image** | docker.io/aquasec/trivy:0.18.1 |

| ENV | VALUE |
| --- | -----  |
|GITHUB_TOKEN | taken from secret with key: ``GITHUB_TOKEN``|
|HTTP_PROXY | |
|HTTPS_PROXY | |
|NO_PROXY | |
|TRIVY_CACHE_DIR | /home/scanner/.cache/trivy|
|TRIVY_DEBUG | False|
|TRIVY_LISTEN | 0.0.0.0:4954|
|TRIVY_SKIP_UPDATE | False|
