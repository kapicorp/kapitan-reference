local kap = import 'lib/kap.libsonnet';
local utils = kap.utils;
local p = kap.parameters;

local ingresses = utils.objectGet(p, 'ingresses', {});

{
  [ingress_name + '-ingress']:
  local ingress = ingresses[ingress_name];
  kap.K8sIngress(ingress_name)
    .WithAnnotations(utils.objectGet(ingress, 'annotations', {}))
    .WithNamespace(p.namespace)
    .WithDefaultBackend(utils.objectGet(ingress, 'backend', {}))
    .WithPaths(utils.objectGet(ingress, 'paths', {}))
  for ingress_name in std.objectFields(ingresses)
} + {
  # see https://github.com/deepmind/kapitan/issues/491
  fixme: {}
}
