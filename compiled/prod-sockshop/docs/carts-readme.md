# Documentation for carts on prod-sockshop

|||
| --- | ---- |
| **Component name** | carts |
| **Application** | sock-shop |
| **Replicas** | 1 |
| **Image** | weaveworksdemos/carts:0.4.8 |

| ENV | VALUE |
| --- | -----  |
|JAVA_OPTS | -Xms64m -Xmx128m -XX:PermSize=32m -XX:MaxPermSize=64m -XX:+UseG1GC -Djava.security.egd=file:/dev/urandom|
|ZIPKIN | zipkin.jaeger.svc.cluster.local|
