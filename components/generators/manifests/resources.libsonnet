local kap = import 'lib/kap.libsonnet';

local utils = kap.utils;
local p = kap.parameters;


{
  SecretVolume(secret, items):: {
    secret: {
      secretName: secret.metadata.name,
      defaultMode: 420,
      items: [{
        key: item,
        path: item,
      } for item in items],
    },
  },

  ConfigVolume(config, items):: {
    configMap: {
      name: config.metadata.name,
      defaultMode: 420,
      items: [{
        key: item,
        path: item,
      } for item in items],
    },
  },

  Container(service_component, config_map_configs, secrets_configs)::
    kap.K8sContainer(service_component.name, service_component, secrets_configs)
    .WithArgs(utils.objectGet(service_component, 'args'))
    .WithCommand(utils.objectGet(service_component, 'command'))
    .WithEnvs(utils.objectGet(service_component, 'env', {}))
    .WithImage(utils.objectGet(service_component, 'image'))
    .WithLivenessProbe(utils.objectGet(service_component, 'healthcheck', { probes: [] }), service_component.healthcheck)
    .WithPorts(utils.objectGet(service_component, 'ports', {}))
    .WithReadinessProbe(utils.objectGet(service_component, 'healthcheck', { probes: [] }), service_component.healthcheck)
    .WithRunAsUser(utils.objectGet(service_component.security, 'user_id'), 'security' in service_component)
    .WithAllowPrivilegeEscalation(utils.objectGet(service_component.security, 'allow_privilege_escalation'), 'security' in service_component)
    .WithMount({ [secret_name]: {
      [if 'subPath' in secrets_configs[secret_name].config then 'subPath']: secrets_configs[secret_name].config.subPath,
      mountPath: secrets_configs[secret_name].config.mount,
      readOnly: true,
    } for secret_name in std.objectFields(secrets_configs) if 'mount' in secrets_configs[secret_name].config }, secrets_configs != null)
    .WithMount({ [config_map_name]: {
      [if 'subPath' in config_map_configs[config_map_name].config then 'subPath']: config_map_configs[config_map_name].config.subPath,
      mountPath: config_map_configs[config_map_name].config.mount,
      readOnly: true,
    } for config_map_name in std.objectFields(config_map_configs) }, config_map_configs != null)
    .WithMount(utils.objectGet(service_component, 'volume_mounts', {}))
    {
      stdin:: super.stdin,
      tty:: super.tty,
      resources: {},
    },


  Service(name, service_component):: kap.K8sService(name)
                                     .WithAnnotations(utils.objectGet(service_component.service, 'annotations', {}))
                                     .WithLabels(utils.objectGet(service_component, 'labels', {}) + { app: service_component.name })
                                     .WithSessionAffinity('None')
                                     .WithExternalTrafficPolicy(utils.objectGet(service_component.service, 'externalTrafficPolicy'))
                                     .WithType(utils.objectGet(service_component.service, 'type'))
                                     .WithPorts(service_component.ports)
                                     {
    workload:: error 'Workload must be set',
    target_pod:: self.workload.spec.template,
  },

  StatefulSet(name, service_component, config_map_configs, secrets_configs)::
    local container = $.Container(service_component, config_map_configs, secrets_configs);
    kap.K8sStatefulSet(name)
    .WithPodAntiAffinity(name, 'kubernetes.io/hostname', utils.objectGet(service_component, 'prefer_pods_in_different_nodes', false))
    .WithNamespace()
    .WithAnnotations(utils.objectGet(service_component, 'annotations', {}))
    .WithContainer({ [service_component.name]: container })
    .WithDNSPolicy(utils.objectGet(service_component, 'dns_policy'))
    .WithLabels(utils.objectGet(service_component, 'labels', {}) + { app: service_component.name })
    .WithMinReadySeconds(utils.objectGet(service_component, 'min_ready_seconds'))
    .WithNamespace(kap.parameters.namespace)
    .WithProgressDeadlineSeconds(utils.objectGet(service_component, 'deployment_progress_deadline_seconds'))
    .WithPrometheusScrapeAnnotation(utils.objectGet(service_component, 'enable_prometheus', false), utils.objectGet(service_component, 'prometheus_port', 6060))
    .WithReplicas(utils.objectGet(service_component, 'replicas', 1))
    .WithRestartPolicy(utils.objectGet(service_component, 'restart_policy', 'Always'))
    .WithServiceAccountName(service_component.name, utils.objectHas(service_component, 'service_account'))
    .WithVolume(utils.objectGet(service_component, 'volumes', {}))
    .WithVolume({ [config_map_name]: $.ConfigVolume(config_map_configs[config_map_name].manifest, config_map_configs[config_map_name].config.items) for config_map_name in std.objectFields(config_map_configs) }, config_map_configs != null)
    .WithVolume({ [secret_name]: $.SecretVolume(secrets_configs[secret_name].manifest, utils.objectGet(secrets_configs[secret_name].config, 'items', [])) for secret_name in std.objectFields(secrets_configs) }, secrets_configs != null)
    .WithVolumeClaimTemplates(utils.objectGet(service_component, 'volume_claims', {}))

  ,
  Deployment(name, service_component, config_map_configs, secrets_configs)::
    local container = $.Container(service_component, config_map_configs, secrets_configs);
    kap.K8sDeployment(name)
    .WithPodAntiAffinity(name, 'kubernetes.io/hostname', utils.objectGet(service_component, 'prefer_pods_in_different_nodes', false))
    .WithPodAntiAffinity(name, 'failure-domain.beta.kubernetes.io/zone', utils.objectGet(service_component, 'prefer_pods_in_different_zones', false))
    .WithNodeAffinity('synthace.com/node-type', utils.objectGet(service_component, 'prefer_pods_in_node_type', 'standard'), 'In', utils.objectHas(service_component, 'prefer_pods_in_node_type', false))
    .WithNamespace()
    .WithAnnotations(utils.objectGet(service_component, 'annotations', {}))
    .WithContainer({ [service_component.name]: container })
    .WithDNSPolicy(utils.objectGet(service_component, 'dns_policy'))
    .WithLabels(utils.objectGet(service_component, 'labels', {}) + { app: service_component.name })
    .WithMinReadySeconds(utils.objectGet(service_component, 'min_ready_seconds'))
    .WithProgressDeadlineSeconds(utils.objectGet(service_component, 'deployment_progress_deadline_seconds'))
    .WithPrometheusScrapeAnnotation(utils.objectGet(service_component, 'enable_prometheus', false), utils.objectGet(service_component, 'prometheus_port', 6060))
    .WithReplicas(utils.objectGet(service_component, 'replicas', 1))
    .WithRestartPolicy(utils.objectGet(service_component, 'restart_policy', 'Always'))
    .WithRollingUpdateStrategy()
    .WithServiceAccountName(service_component.name, utils.objectHas(service_component, 'service_account'))
    .WithVolume(utils.objectGet(service_component, 'volumes', {}))
    .WithVolume({ [config_map_name]: $.ConfigVolume(config_map_configs[config_map_name].manifest, config_map_configs[config_map_name].config.items) for config_map_name in std.objectFields(config_map_configs) }, config_map_configs != null)
    .WithVolume({ [secret_name]: $.SecretVolume(secrets_configs[secret_name].manifest, secrets_configs[secret_name].config.items) for secret_name in std.objectFields(secrets_configs) }, secrets_configs != null)
  ,

  Bundle():: {
    bundle: [],
    WithItem(name, object, enabled=true):: self + if enabled then { [name]: object } else {},
    WithBundled(name, object, enabled=true):: self + if enabled then { bundle+: [object] } else {},
  },

  ServiceManifestSet(service_component)::
    local has_configmaps = utils.objectHas(service_component, 'config_maps');
    local has_service = utils.objectHas(service_component, 'service');
    local has_secrets = utils.objectHas(service_component, 'secrets');
    local has_service_account = utils.objectHas(service_component, 'service_account', false);

    local secrets_config = utils.objectGet(service_component, 'secrets', {});
    local secrets_config_job = utils.objectGet(service_component.migration, 'secrets', {});

    local config_map_config = utils.objectGet(service_component, 'config_maps', {});


    local MergeConfig(name, object, generating_class) = {
      name:: if std.length(object) == 1 then service_component.name else '%s-%s' % [service_component.name, name],
      manifest: generating_class(self.name, object[name].data)
                .WithNamespace(),
      config: { items: [] } + object[name],
    };

    local CreateConfigDefinition(object_config, generating_class) = {
      [name]: MergeConfig(name, object_config, generating_class)
      for name in std.objectFields(object_config)
    };

    local secrets_objects = CreateConfigDefinition(secrets_config, kap.K8sSecret);
    local secrets_manifests = [secret.manifest for secret in utils.objectValues(secrets_objects)];

    local config_map_objects = CreateConfigDefinition(config_map_config, kap.K8sConfigMap);
    local config_map_manifests = [config_map.manifest for config_map in utils.objectValues(config_map_objects)];

    local workload_type = utils.objectGet(service_component, 'type', 'deployment');
    local workload = if workload_type == 'deployment' then
      $.Deployment(service_component.name, service_component, config_map_objects, secrets_objects)
    else if workload_type == 'statefulset' then
      $.StatefulSet(service_component.name, service_component, config_map_objects, secrets_objects);
    local service = if has_service then $.Service(service_component.name, service_component).WithNamespace() + { workload:: workload };


    local serviceAccount = kap.ServiceAccount(service_component.name) {
      metadata+: {
        namespace: p.namespace,
      },
    };

    local vpa_mode = utils.objectGet(service_component, 'vpa', 'Auto');
    local vpa = kap.createVPAFor(workload, mode=vpa_mode) {
      spec+: {
        resourcePolicy+: {
          containerPolicies+: [{
            containerName: 'istio-proxy',
            mode: 'Off',
          }],
        },
      },
    };

    local pdb = kap.PodDisruptionBudget(service_component.name) {
      target_pod:: workload.spec.template,
      spec+: {
        minAvailable: utils.objectGet(service_component, 'pdb_min_available'),
      },
    };


    $.Bundle()
    .WithItem('config', config_map_manifests, has_configmaps)
    .WithItem('secret', secrets_manifests, has_secrets)
    .WithBundled('workload', workload)
    .WithBundled('sa', serviceAccount, has_service_account)
    .WithBundled('vpa', vpa, utils.objectHas(service_component, 'vpa', false))
    .WithBundled('pdb', pdb, utils.objectHas(service_component, 'pdb_min_available'))
    .WithBundled('service', service),
}
