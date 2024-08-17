# Kapitan Reference Setup

[![CI](https://github.com/kapicorp/kapitan-reference/actions/workflows/integration-test.yml/badge.svg?event=push)](https://github.com/kapicorp/kapitan-reference/actions/workflows/integration-test.yml)

This repository is meant to be a way to bootstrap your [Kapitan](https://kapitan.dev) setup to get you up and running.

It is meant to help you make use of best practices and libraries that can make Kapitan the ultimate tool for all your configuration needs.

Look at the branch [`init`](https://github.com/kapicorp/kapitan-reference/tree/init) for a clean setup with only the basics enabled.


## Quickstart

```shell script
$ git clone git@github.com:kapicorp/kapitan-reference.git kapitan-templates
$ cd kapitan-templates

$ ./kapitan compile
Rendered inventory (3.45s)
Compiled pritunl (0.23s)
Compiled vault (0.27s)
Compiled examples (0.28s)
Compiled gke-pvm-killer (0.10s)
Compiled mysql (0.10s)
Compiled postgres-proxy (0.11s)
Compiled sock-shop (0.23s)
Compiled echo-server (0.11s)
Compiled global (0.09s)
Compiled guestbook-argocd (0.12s)
Compiled tutorial (0.15s)
Compiled kapicorp-project-123 (0.09s)
Compiled kapicorp-terraform-admin (0.10s)
Compiled tesoro (0.13s)
Compiled dev-sockshop (0.24s)
Compiled prod-sockshop (0.27s)
Compiled argocd (0.99s)
Compiled github-actions (6.99s)
```

## Generators documentation (IN PROGRESS)

[generators.kapitan.dev](https://generators.kapitan.dev/)

### Tools

This repo comes already with some helper tools. We will expand it as the time goes.

For now, you can see that the [`./kapitan`](kapitan) file is a wrapper script that allows you to run kapitan without installing any binary (it does depends on docker!)


| Script    | Description                      |
|-----------|----------------------------------|
| ./kapitan | Wrapper script to invoke kapitan |


### Libraries

This repo already packs some important libraries that you will want to have when working with kapitan.

| Name    | Description            | Inventory file                                       |
|---------|------------------------|------------------------------------------------------|
| kgenlib | Kapitan Generators SKD | [kgenlib.yml](inventory/classes/kapitan/generators/kgenlib.yml) |


### External Dependencies

Kapitan allows you to manage external dependencies like the above libraries.
This repo enables fetching by default through the `.kapitan` file, which only fetches missing dependencies.

```yaml
version: 0.32
compile:
  prune: true
  embed-refs: true
  fetch: true    # Automatically fetches missing dependencies.
```

To update them from the upstream version, force fetch by running:

```shell script
./kapitan compile --force-fetch
Dependency https://github.com/kapicorp/generators.git: saved to system/lib
Dependency https://github.com/kapicorp/generators.git: saved to system/generators/kubernetes
Dependency https://github.com/kapicorp/generators.git: saved to system/generators/terraform
Dependency argo-cd: saved to system/sources/charts/argo-cd/argo-cd/3.32.0/v2.2.3
Rendered inventory (3.45s)
Compiled vault (0.27s)
Compiled pritunl (0.27s)
Compiled examples (0.32s)
Compiled gke-pvm-killer (0.10s)
Compiled mysql (0.10s)
Compiled postgres-proxy (0.10s)
Compiled sock-shop (0.23s)
Compiled echo-server (0.11s)
Compiled global (0.09s)
Compiled tutorial (0.14s)
Compiled guestbook-argocd (0.11s)
Compiled kapicorp-project-123 (0.09s)
Compiled kapicorp-terraform-admin (0.09s)
Compiled tesoro (0.13s)
Compiled dev-sockshop (0.24s)
Compiled prod-sockshop (0.27s)
Compiled argocd (0.97s)
Compiled github-actions (7.13s)
```
