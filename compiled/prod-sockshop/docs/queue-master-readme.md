# Documentation for queue-master on prod-sockshop

|||
| --- | ---- |
| **Component name** | queue-master |
| **Application** | sock-shop |
| **Replicas** | 1 |
| **Image** | weaveworksdemos/queue-master:0.3.1 |

| ENV | VALUE |
| --- | -----  |
|JAVA_OPTS | -Xms64m -Xmx128m -XX:PermSize=32m -XX:MaxPermSize=64m -XX:+UseG1GC -Djava.security.egd=file:/dev/urandom|
|ZIPKIN | zipkin.jaeger.svc.cluster.local|
