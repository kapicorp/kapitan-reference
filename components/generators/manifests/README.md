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

## Defaults

Sometimes, when defining many components, you and up repeating lots of similar configurations.
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
 
 
