# Ingresses generator

The `ingresses` generator adds on the manifest generator by providing a quick way to expose paths to your application using ingresses resources.

## Basic usage

The generator is expecting ingresses to be defined under the `parameters.ingresses` path of the inventory.

For convenience, you can add the configuration in the same files as your component.

For instance, add the following to the component [echo-server](inventory/classes/components/echo-server.yml).

```yaml
  ingresses:
    global:
      annotations:
        kubernetes.io/ingress.global-static-ip-name: my_static_ip
      paths:
        - backend:
            serviceName: echo-server
            servicePort: 80
          path: /echo/*
```

which will generate a file similar to:

```yaml
apiVersion: networking.k8s.io/v1beta1
kind: Ingress
metadata:
  annotations:
    kubernetes.io/ingress.global-static-ip-name: my_static_ip
  labels:
    name: global
  name: global
  namespace: tutorial
spec:
  rules:
    - http:
        paths:
          - backend:
              serviceName: echo-server
              servicePort: 80
            path: /echo/*
```

Injecting "rules" confirations is also supported:

```yaml
  ingresses:
    global:
      annotations:
        kubernetes.io/ingress.global-static-ip-name: my_static_ip
      rules:
      - http:
          paths:
          - backend:
            serviceName: echo-server
            servicePort: 80
            path: /echo/*
```

## TODO:
* Support for GKE managed certificates
* Support for TLS secrets