# Documentation for pritunl-mongo on pritunl

|||
| --- | ---- |
| **Component name** | pritunl-mongo |
| **Application** | Not Defined |
| **Replicas** | 1 |
| **Image** | docker.io/bitnami/mongodb:4.2.6-debian-10-r23 |

| ENV | VALUE |
| --- | -----  |
|MONGODB_DATABASE | pritunl|
|MONGODB_DISABLE_SYSTEM_LOG | False|
|MONGODB_ENABLE_DIRECTORY_PER_DB | False|
|MONGODB_ENABLE_IPV6 | False|
|MONGODB_PASSWORD | _3sbjfMZm3GOcfIu7c_bKdmzZuc_gO0Dgn6CfKbYMgk|
|MONGODB_ROOT_PASSWORD | taken from secret with key: ``mongodb-root-password``|
|MONGODB_SYSTEM_LOG_VERBOSITY | 0|
|MONGODB_USERNAME | pritunl|
