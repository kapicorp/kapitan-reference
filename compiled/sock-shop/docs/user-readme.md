# Documentation for user on sock-shop

|||
| --- | ---- |
| **Component name** | user |
| **Application** | Not Defined |
| **Replicas** | 1 |
| **Image** | weaveworksdemos/user:0.4.7 |

| ENV | VALUE |
| --- | -----  |
|JAVA_OPTS | -Xms64m -Xmx128m -XX:PermSize=32m -XX:MaxPermSize=64m -XX:+UseG1GC -Djava.security.egd=file:/dev/urandom|
|ZIPKIN | zipkin.jaeger.svc.cluster.local|
