# Manifest Generator

The manifest generator allows to quickly generate Kubernetes manifests.

The schema of the component definition is available here:
[schema](https://kapicorp.github.io/kapitan-reference/components/generators/manifests/target/)

## Basic usage

The generator is expecting components to be defined under the `parameters.components` path of the inventory.

For instance, create a component `nginx`, simply create the following section:

```yaml
parameters:
  components:
    nginx:
      image: nginx
```

Compiling, `kapitan` will generate a simple deployment with the above image.

## Defaults

Sometimes, when defining many components, you and up repeating lots of similar configurations.
With this generator, you can define defaults in 2 ways:

### Global Generator Defaults
The [global defaults](inventory/classes/kapitan/generators/manifests.yml) can be used to set defaults for every component being generated.
  As you can see, some defaults are already set (e.g. `type: deployment`)
  
### Application defaults
You can also create application defaults, where an application is a class/profile of components.

For instance, let's assume you have the following definition for an application class called `microservices`

```yaml
parameters:
  applications:
    microservices:
      component_defaults:
        replicas: 3
        env:
          APPLICATION: microservice
```

Every component that belongs to that application class will receive the defaults for the application.
To associate a component to an application, use the `application` directive.

```yaml
parameters:
  components:
    nginx:
      application: microservices
      image: nginx
```

