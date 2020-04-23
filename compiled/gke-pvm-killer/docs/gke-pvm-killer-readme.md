# Documentation for gke-pvm-killer on gke-pvm-killer

|||
| --- | ---- |
| **Component name** | gke-pvm-killer |
| **Application** | Not Defined |
| **Replicas** | 1 |
| **Image** | estafette/estafette-gke-preemptible-killer:1.2.5 |

| ENV | VALUE |
| --- | -----  |
|DRAIN_TIMEOUT | 300|
|GOOGLE_APPLICATION_CREDENTIALS | /opt/secrets/service_account_file|
|INTERVAL | 600|
