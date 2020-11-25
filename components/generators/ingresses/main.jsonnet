local kap = import 'lib/kap.libsonnet';
local utils = kap.utils;
local p = kap.parameters;

local ingresses = utils.objectGet(p, 'ingresses', {});

//Support for GKE managed certificates

local managedcertificates = {
  [ingress_name + '-managed-certificate']:
    local ingress = p.ingresses[ingress_name];
    local is_managed_certificates = utils.objectGet(ingress, 'gke_managed_certificates', false);
    if is_managed_certificates then kap.K8sGKEManagedCertificate(ingress.domains[0])
                                    {
      spec+: {
        domains: ingress.domains,
      },
    }
                                    .WithNamespace(p.namespace) else {}
  for ingress_name in std.objectFields(ingresses)
};


{
  [ingress_name + '-ingress']:
    local ingress = ingresses[ingress_name];
    kap.K8sIngress(ingress_name)
    .WithAnnotations(utils.objectGet(ingress, 'annotations', {}))
    .WithNamespace(p.namespace)
    .WithDefaultBackend(utils.objectGet(ingress, 'default_backend', {}))
    .WithPaths(utils.objectGet(ingress, 'paths', []))
    .WithRules(utils.objectGet(ingress, 'rules', []))
  for ingress_name in std.objectFields(ingresses)
} + managedcertificates + {
  // see https://github.com/deepmind/kapitan/issues/491
  fixme: {},
}
