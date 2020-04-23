# Documentation for mysql on mysql

| --- | ---- |
| **Component name** | mysql |
| **Application** | Not Defined |
| **Replicas** | 1 |
| **Image** | mysql:5.7.28 |

| ENV | VALUE |
| --- | -----  |
|MYSQL_DATABASE | |
|MYSQL_PASSWORD | taken from secret with key: ``mysql-password``|
|MYSQL_ROOT_PASSWORD | taken from secret with key: ``mysql-root-password``|
|MYSQL_USER | |
