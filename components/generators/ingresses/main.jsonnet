local kap = import 'lib/kap.libsonnet';
local utils = kap.utils;
local p = kap.parameters;

local ingresses = utils.objectGet(p, 'ingresses', {});

//Support for GKE managed certificates
local ingresses_with_managed_certificates = utils.objectGet(ingresses, 'gke_managed_certificates', false);
local managedcertificates = if ingresses_with_managed_certificates then {
  [ingress_name + '-managed-certificate']:
  local ingress = p.ingresses[ingress_name];
  kap.K8sGKEManagedCertificate(ingress.domains[0])
    .WithNamespace(p.namespace)
    .WithDomains(ingress.domains)
  for ingress_name in std.objectFields(p.ingresses)
} else {};


{
  [ingress_name + '-ingress']:
  local ingress = ingresses[ingress_name];
  kap.K8sIngress(ingress_name)
    .WithAnnotations(utils.objectGet(ingress, 'annotations', {}))
    .WithNamespace(p.namespace)
    .WithDefaultBackend(utils.objectGet(ingress, 'backend', {}))
    .WithPaths(utils.objectGet(ingress, 'paths', {}))
    .WithRules(utils.objectGet(ingress, 'rules', []))
  for ingress_name in std.objectFields(ingresses)
} + managedcertificates + {
  # see https://github.com/deepmind/kapitan/issues/491
  fixme: {}
}