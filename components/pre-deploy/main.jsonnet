local kap = import 'lib/kap.libsonnet';
local p = kap.parameters;

local namespace = kap.utils.objectGet(p, 'namespace', 'default');
{
  [namespace + '-namespace']: kap.Namespace(namespace),
}
