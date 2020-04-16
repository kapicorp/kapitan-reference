# Kapitan Reference Setup

This repository is meant to be a way to bootstrap your [Kapitan](https://kapitan.dev) setup to get you up and running.

It is meant to help you make use of best practices and libraries that can make Kapitan the ultimate tool for all your configuration needs.

## Quickstart

```shell script
$ git clone git@github.com:kapicorp/kapitan-reference.git kapitan-templates
$ cd kapitan-templates

$ ./kapitan compile
Compiled echo-server (0.29s)
Compiled mysql (0.36s)
``` 

## Slow walk-through

### Tools

This repo comes already with some helper tools. We will expand it as the time goes.

For now, you can see that the [`./kapitan`](kapitan) file is a wrapper script that allows you to run kapitan without installing any binary (it does depends on docker!)

*Note*: For speed, if kapitan is already installed, it will prefer the non-docker version.

| Script | Description |
| ------ | ----------- |
| ./kapitan | Wrapper script to invoke kapitan |
| [generate_sa_secrets.sh](templates/scripts/generate_sa_secrets.sh) | Templated script to automatically inject service accounts into refs |
| [import_kubernetes_cluster.sh](scripts/import_kubernetes_cluster.sh) | Helper scripts that looks for GKE cluster and automatically imports them into the inventory |

### Libraries

This repo already packs some important libraries that you will want to have when working with kapitan.

| Name | Description | Inventory file |
| ---- | ----------- | -------------- |
| [kube-libsonnet](https://github.com/bitnami-labs/kube-libsonnet) | bitnami-labs kube library | [kube.yml](inventory/classes/kapitan/kube.yml) |
| [sponnet](https://github.com/spinnaker/sponnet) | Jsonnet library specifically for Spinnaker | [spinnaker.yml](inventory/classes/kapitan/spinnaker.yml)|
| [manifests-generator](components/generators/manifests) | [Synthace](www.synthace.com) manifests generator | [generators/manifests.yml](inventory/classes/kapitan/generators/manifests.yml)|
| [utils](lib/utils.libjsonnet) | helpful utilites ||
| [kap](lib/kap.libjsonnet) | Kapitan boilerplate in one file ||
| [service_components](lib/service_components.libjsonnet)| Library used by multiple generators ||

Kapitan allows you to manage external dependencies like the above libraries.
For instance, in the  [spinnaker.yml](inventory/classes/kapitan/spinnaker.yml) file, the "dependencies" directive tells Kapitan where to find the library.

To update them, run:

```shell script
./kapitan compile --fetch
Dependency lib/kube.libjsonnet : already exists. Ignoring
Dependency lib/spinnaker-pipeline.libjsonnet : already exists. Ignoring
Dependency lib/spinnaker-application.libjsonnet : already exists. Ignoring
Compiled echo-server (0.31s)
Compiled mysql (0.37s)
``` 

## Generators

As explained in the blog post [Keep your ship together with Kapitan](https://medium.com/kapitan-blog/keep-your-ship-together-with-kapitan-d82d441cc3e7). generators are a 
powerful idea to simplify the management your setup.

We will release initially generators for kubernetes manifests, terraform and spinnaker pipelines.

For now, only the manifest generator is available

### Manifests generator

The manifests generator allows you to quickly generate Kubernetes manifests from a much simpler yaml configuration.

The aim for this approach is to allow you to cover the vast majority of the needs you will have for your components.
More complex scenarios can also be achieved by expanding the library, or implementing your own template.

### Examples
To help you get started, please look at the following examples:

| source | description | output |
| ------ | ----------- | ------ |
|[mysql](inventory/classes/components/mysql.yml)| Example MySQL statefulset | [manifests](compiled/mysql/manifests)|
|[echo-server](inventory/classes/components/echo-server.yml)| Example using [echo-server](https://github.com/jmalloc/echo-server) | [manifests](compiled/echo-server/manifests)|
|[gke-pvm-killer](inventory/classes/components/gke-pvm-killer.yml)| Example using [estafette-gke-preemptible-killer](https://github.com/estafette/estafette-gke-preemptible-killer)| [manifests](compiled/gke-pvm-killer/manifests)|

Please find the generated manifests in the [compiled](compiled) folder

### Request or submit your examples
We have used this generator extensively, and we know it covers the majority of the use cases.
If you want a specific example, please let us know (or submit your PR)

By adding more example we will be able to stress test the library to make sure we really satisfy all the most common use cases.


[Documentation](components/generators/manifests/README.md) [TBD]
