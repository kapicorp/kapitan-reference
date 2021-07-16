# Cert-Manager

# 2021-07-16
```shell
helm template cert-manager --values components/helm/cert-manager/1.4.0/values.yml --create-namespace --namespace cert-manager --version v1.4.0 jetstack/cert-manager > components/helm/cert-manager/1.4.0/cert-manager.rendered.yml
```
