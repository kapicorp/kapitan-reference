local kap = import 'lib/kap.libsonnet';
local utils = kap.utils;
local p = kap.parameters;
local SCHEMAS = import 'components/generators/manifests/schemas.libsonnet';

local fallback_service_config = utils.objectGet(p.generators.manifest, 'default_config', {});

local default_config_by_app = {
  [app_name]: utils.objectGet(p.applications[app_name], 'component_defaults', {})
  for app_name in std.objectFields(utils.objectGet(p, 'applications', {}))
};


local ServiceComponent = function(component_name, component_data)

  local application = utils.objectGet(component_data, 'application', '');
  local application_defaults = utils.objectGet(default_config_by_app, application, {});
  local all_defaults = std.mergePatch(fallback_service_config, application_defaults);
  local component_data_with_defaults = std.mergePatch(all_defaults, component_data);

  local final_component_data = component_data_with_defaults {
    name: utils.objectGet(component_data, 'name', component_name),
  };

  local validation = kap.jsonschema(final_component_data, SCHEMAS.service_component);
  assert validation.valid : 'Could not validate %s: %s' % [component_name, validation.reason];

  final_component_data
;

{
  [component_name]: ServiceComponent(component_name, p.components[component_name])
  for component_name in std.objectFields(utils.objectGet(p, 'components', {}))
}
