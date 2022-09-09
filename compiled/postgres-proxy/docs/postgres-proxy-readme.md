# Documentation for postgres-proxy on postgres-proxy

|||
| --- | ---- |
| **Component name** | postgres-proxy |
| **Application** | Not Defined |
| **Replicas** | 3 |
| **Image** | gcr.io/cloudsql-docker/gce-proxy:1.16 |

| ENV | VALUE |
| --- | -----  |
|CLOUDSQL_INSTANCE_NAME | example:instance|
|GOOGLE_APPLICATION_CREDENTIALS | /opt/secrets/service_account_file|
