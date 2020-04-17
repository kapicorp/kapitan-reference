# Manifest Generator

The manifest generator allows to quickly generate Kubernetes manifests.

The schema of the component definition is available here:
[schema](https://kapicorp.github.io/kapitan-reference/components/generators/manifests/target/)

## Basic usage

The generator is expecting components to be defined under the `parameters.components` path of the inventory.

For instance, create a component `echo-server`, simply create the following section:

```yaml
parameters:
  components:
    echo-server:
      image: jmalloc/echo-server
```

Compiling, `kapitan` will generate a simple deployment with the above image.

## Defining default values

Sometimes, when defining many components, you and up repeating many repeating configurations.
With this generator, you can define defaults in 2 ways:

### Global Generator Defaults
The [global defaults](../../../inventory/classes/kapitan/generators/manifests.yml) can be used to set defaults for every component being generated.

As you can see, some defaults are already set:
```yaml
  generators:
    manifest:
      default_config:
        type: deployment
        annotations:
          "manifests.kapicorp.com/generated": true
```
  
  
### Application defaults
You can also create application defaults, where an application is a class/profile that can be associated to multiple components.

For instance, let's assume you have the following definition for an application class called `microservices`

```yaml
parameters:
  applications:
    microservices:
      component_defaults:
        replicas: 3
        env:
          KAPITAN_APPLICATION: microservices
```

Every component that belongs to that application class will receive the defaults for the application.
To associate a component to an application, use the `application` directive.

```yaml
parameters:
  components:
    echo-server:
      application: microservices
      image: jmalloc/echo-server
```

Compiling, kapitan will generate a *deployment* with image `jmalloc/echo-server`, 3 replicas, an annotation and an env variable.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  annotations:
    manifests.kapicorp.com/generated: 'true'
  labels:
    app: echo-server
  name: echo-server
  namespace: tutorial
spec:
  replicas: 3
  selector:
    matchLabels:
      app: echo-server
  strategy:
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 1
    type: RollingUpdate
  template:
    metadata:
      labels:
        app: echo-server
    spec:
      containers:
        - env:
            - name: KAPITAN_APPLICATION
              value: microservices
          image: jmalloc/echo-server
          imagePullPolicy: IfNotPresent
          name: echo-server
      restartPolicy: Always
      terminationGracePeriodSeconds: 30
```

## Ports and Services

### Defining ports
You can define the ports your component uses by adding them under the `ports` directive:

```yaml
parameters:
  components:
    echo-server:
      <other config>
      ports:
        http:
          container_port: 8080
```

The above will produce the following effect:

```diff
--- a/compiled/echo-server/manifests/echo-server-bundle.yml
+++ b/compiled/echo-server/manifests/echo-server-bundle.yml
@@ -38,6 +38,10 @@ spec:
         - image: jmalloc/echo-server
           imagePullPolicy: IfNotPresent
           name: echo-server
+          ports:
+            - containerPort: 8080
+              name: http
+              protocol: TCP

```

### Exposing a service
If you want to expose the service, add the `service` directive with the desired service `type`, and define the `service_port`:

```yaml
parameters:
  components:
    echo-server:
      <other config>
      ports:
        http:
          service_port: 80
          container_port: 8080
```

Which will create a service manifest with the same name as the component, and will produce the following effect:
```diff
--- a/compiled/echo-server/manifests/echo-server-bundle.yml
+++ b/compiled/echo-server/manifests/echo-server-bundle.yml
@@ -52,3 +52,21 @@ metadata:
     name: echo-server
   name: echo-server
   namespace: echo-server
+---
+apiVersion: v1
+kind: Service
+metadata:
+  labels:
+    app: echo-server
+  name: echo-server
+  namespace: echo-server
+spec:
+  ports:
+    - name: http
+      port: 80
+      protocol: TCP
+      targetPort: http
+  selector:
+    app: echo-server
+  sessionAffinity: None
+  type: LoadBalancer
```

### Liveness and Readiness checks
You can also quickly add a `readiness`/`liveness` check:

```yaml
parameters:
  components:
    echo-server:
      <other config>
      healthcheck:
        type: http
        port: http
        probes: ['readiness']
        path: /_health
        timeout_seconds: 3
```

which produces:
```diff
--- a/compiled/echo-server/manifests/echo-server-bundle.yml
+++ b/compiled/echo-server/manifests/echo-server-bundle.yml
@@ -42,6 +42,15 @@ spec:
             - containerPort: 8080
               name: http
               protocol: TCP
+          readinessProbe:
+            failureThreshold: 3
+            httpGet:
+              path: /_health
+              port: http
+              scheme: HTTP
+            periodSeconds: 10
+            successThreshold: 1
+            timeoutSeconds: 3
```

## Config Maps

Creating secrets and config is very simple with Kapitan, and the interface is very similar with minor differences.

### Simple config

```yaml
      config_maps:
        config:
          data:
            echo-service.conf: 
              value: |-
                # A configuration file
                example: true
```

A configMap manifest was created. The name is taken from the component.

```yaml
cat compiled/tutorial/manifests/echo-server-config.yml
apiVersion: v1
data:
  echo-service.conf: '# A configuration file

    example: true'
kind: ConfigMap
metadata:
  labels:
    name: echo-server
  name: echo-server
  namespace: tutorial
```

### Mounting a config map
Note that in the previous example the config map is not mounted, because the `mount` directive is missing.

```yaml
      config_maps:
        config:
          mount: /opt/echo-service
          data:
            echo-service.conf: 
              value: |-
                # A configuration file
                example: true
```

Simply adding the above configuration, will immediately configure the component to mount the config map we have just defined:

```diff
+          volumeMounts:
+            - mountPath: /opt/echo-service
+              name: config
+              readOnly: true
       restartPolicy: Always
       terminationGracePeriodSeconds: 30
+      volumes:
+        - configMap:
+            defaultMode: 420
+            name: echo-server
+          name: config
```

### Templated config
A more advanced way to create the configuration file, is to use an external `jinja` file as source:

```yaml
      config_maps:
        config:
          mount: /opt/echo-service
          data:
            echo-service.conf:
              template: 'components/echo-server/echo-server.conf.j2'
              values:
                example: true
```

with the file [echo-server.conf.j2](../../../components/echo-server/echo-server.conf.j2) being a jinja template file. 

As expected, we can inject any value from the inventory into the the file.

### Filtering files to mount

We do not always expect to mount all files available in a config map. Sometimes in the config map we have a mix of files and other values destined to be consumed by environment variables instead.

For instance, given the following setup, we can restrict the mount only to files defined in the `items` directive:

```yaml
      config_maps:
        config:
          mount: /opt/echo-service
          items:
            - echo-service.conf
          data:
            echo-service.conf:
              template: 'components/echo-server/echo-server.conf.j2'
              values:
                example: true
            simple_config:
              value: "not mounted"
```

the diff shows that the generator makes use of the items directive in the manifest:

```diff
--- a/compiled/echo-server/manifests/echo-server-config.yml
+++ b/compiled/echo-server/manifests/echo-server-bundle.yml
@@ -60,6 +60,9 @@ spec:
       volumes:
         - configMap:
             defaultMode: 420
+            items:
+              - key: echo-service.conf
+                path: echo-service.conf
             name: echo-server
```

## Secrets

What discussed with Config Maps also applies to Secrets.
However, in the case of secrets, we have a coupld of extra features:

### Auto base64 encode

We can automatically base64 encode secrets that are not already encoded:
```yaml
      secrets:
        secret:
          data:
            encoded_secret:
              value: my_secret
              b64_encode: true
```

```yaml
cat compiled/tutorial/manifests/echo-server-secret.yml
apiVersion: v1
data:
  encoded_secret: bXlfc2VjcmV0    # ENCODED my_secret
kind: Secret
metadata:
  labels:
    name: echo-server
  name: echo-server
  namespace: tutorial
type: Opaque

```
Note that, because the mount directive is missing, the secret will not be mounted automatically.

