# Documentation for vault on examples

|||
| --- | ---- |
| **Component name** | vault |
| **Application** | Not Defined |
| **Replicas** | 3 |
| **Image** | vault:1.7.3 |

| ENV | VALUE |
| --- | -----  |
|HOME | /home/vault|
|HOST_IP | UNMATCHED {'fieldRef': {'fieldPath': 'status.hostIP'}}|
|HOSTNAME | UNMATCHED {'fieldRef': {'fieldPath': 'metadata.name'}}|
|POD_IP | UNMATCHED {'fieldRef': {'fieldPath': 'status.podIP'}}|
|SKIP_CHOWN | true|
|SKIP_SETCAP | true|
|VAULT_ADDR | http://127.0.0.1:8200|
|VAULT_API_ADDR | http://$(POD_IP):8200|
|VAULT_CLUSTER_ADDR | https://$(HOSTNAME):8201|
|VAULT_K8S_NAMESPACE | UNMATCHED {'fieldRef': {'fieldPath': 'metadata.namespace'}}|
|VAULT_K8S_POD_NAME | UNMATCHED {'fieldRef': {'fieldPath': 'metadata.name'}}|
