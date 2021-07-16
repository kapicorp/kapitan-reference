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

### Create an ingress resource

Each key under the `ingresses` parameters represent an ingress resource:

```yaml
parameters:
---
ingresses:
  main:
    default_backend:
      name: frontend
      port: 80
```

Will generate the following `Ingress` resource

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  labels:
    name: main
  name: main
  namespace: prod-sockshop
spec:
  backend:
    serviceName: frontend
    servicePort: 80
```

### Add annotations to an ingress

Simply adding the `annotations` directive allows to configure an ingress:

```yaml
ingresses:
  main:
    annotations:
      kubernetes.io/ingress.global-static-ip-name: static-ip-name
    default_backend:
      name: frontend
      port: 80
```

The generator will add the annotations to the resource

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  annotations:
    kubernetes.io/ingress.global-static-ip-name: static-ip-name
  labels:
    name: main
  name: main
  namespace: prod-sockshop
spec:
  backend:
    serviceName: frontend
    servicePort: 80
```

## Adding TLS certificates

You can define a TLS certificate to be used by the ingress with the following syntax

```yaml
generators:
  kubernetes:
    secrets:
      sockshop.kapicorp.com:
        type: kubernetes.io/tls
        data:
          tls.crt:
            value: ?{gkms:targets/${target_name}/sockshop.kapicorp.com.crt}
          tls.key:
            value: ?{gkms:targets/${target_name}/sockshop.kapicorp.com.key}
```

Both references need to be configured before hand with the correct PEM certificates.

You can then pass the TLS configuration to the ingress, with a reference to the secret just created:

```yaml
  ingresses:
    global:
      annotations:
        kubernetes.io/ingress.global-static-ip-name: sock-shop-prod
      default_backend:
        name: frontend
        port: 80
      tls:
      - hosts:
          - sockshop.kapicorp.com
        secretName: sockshop.kapicorp.com
```

## Managed certificats (currently GKE only)

### Add a managed certificate

Set the `manage_certificate` directive to the domain you want to manage a certificate for.

```yaml
ingresses:
  main:
    managed_certificate: sockshop.kapicorp.com
    annotations:
      kubernetes.io/ingress.global-static-ip-name: static-ip-name
    default_backend:
      name: frontend
      port: 80
```

Which will create a new `ManagedCertificate` resource for such domain

```yaml
apiVersion: networking.gke.io/v1beta1
kind: ManagedCertificate
metadata:
  labels:
    name: sockshop.kapicorp.com
  name: sockshop.kapicorp.com
  namespace: prod-sockshop
spec:
  domains:
    - sockshop.kapicorp.com
```

and injects the correct annotation into the ingress resource:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  annotations:
    kubernetes.io/ingress.global-static-ip-name: static-ip-name
    networking.gke.io/managed-certificates: sockshop.kapicorp.com
  labels:
    name: main
  name: main
  namespace: prod-sockshop
spec:
  backend:
    serviceName: frontend
    servicePort: 80
```

### Multiple certificats

The generator also supports multiple certificates with the `additional_domains` directive.

```yaml
ingresses:
  main:
    annotations:
      kubernetes.io/ingress.global-static-ip-name: static-ip-name
    managed_certificate: sockshop.kapicorp.com
    additional_domains:
      - secure.kapicorp.com
    default_backend:
      name: frontend
      port: 80
```

Which will generate:

```yaml
apiVersion: networking.gke.io/v1beta1
kind: ManagedCertificate
metadata:
  labels:
    name: sockshop.kapicorp.com
  name: sockshop.kapicorp.com
  namespace: prod-sockshop
spec:
  domains:
    - sockshop.kapicorp.com
    - secure.kapicorp.com
```
