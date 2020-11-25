local kap = import 'lib/kap.libsonnet';
local prom = import 'lib/prometheus-operator.libjsonnet';

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

  Container(name, container_definition, config_map_configs, secrets_configs)::
    kap.K8sContainer(name, container_definition, secrets_configs)
    .WithArgs(utils.objectGet(container_definition, 'args'))
    .WithCommand(utils.objectGet(container_definition, 'command'))
    .WithEnvs(utils.objectGet(container_definition, 'env', {}))
    .WithImage(utils.objectGet(container_definition, 'image'))
    .WithLivenessProbe(utils.objectGet(container_definition, 'healthcheck', {}), container_definition.healthcheck)
    .WithPullPolicy(utils.objectGet(container_definition, 'pull_policy', "IfNotPresent"))
    .WithPorts(utils.objectGet(container_definition, 'ports', {}))
    .WithReadinessProbe(utils.objectGet(container_definition, 'healthcheck', {}), container_definition.healthcheck)
    .WithRunAsUser(utils.objectGet(container_definition.security, 'user_id'), 'security' in container_definition)
    .WithSecurityContext(utils.objectGet(container_definition, 'security_context', {}))
    .WithAllowPrivilegeEscalation(utils.objectGet(container_definition.security, 'allow_privilege_escalation'), 'security' in container_definition)
    .WithMount({
      local config = utils.objectGet(utils.objectGet(container_definition, 'secrets', {}), name, secrets_configs[name].config), 
      [name]: {
        subPath: utils.objectGet(config, 'subPath'),
        mountPath: utils.objectGet(config, 'mount'),
        readOnly: true,
    } for name in std.objectFields(secrets_configs) if 'mount' in utils.objectGet(utils.objectGet(container_definition, 'secrets', {}), name, secrets_configs[name].config)} , secrets_configs != null)
    .WithMount({ 
      local config = utils.objectGet(utils.objectGet(container_definition, 'config_maps', {}), name, config_map_configs[name].config), 
      [name]: {
        subPath: utils.objectGet(config, 'subPath'),
        mountPath: utils.objectGet(config, 'mount'),
        readOnly: true,
    } for name in std.objectFields(config_map_configs) }, config_map_configs != null)
    .WithMount(utils.objectGet(container_definition, 'volume_mounts', {}))
    .WithResources(utils.objectGet(container_definition, 'resources', {}))
    {
      stdin:: super.stdin,
      tty:: super.tty,
    },


  Service(name, service_component):: kap.K8sService(name)
                                     .WithAnnotations(utils.objectGet(service_component.service, 'annotations', {}))
                                     .WithLabels(utils.objectGet(service_component, 'labels', {}))
                                     .WithSessionAffinity('None')
                                     .WithExternalTrafficPolicy(utils.objectGet(service_component.service, 'externalTrafficPolicy'))
                                     .WithType(utils.objectGet(service_component.service, 'type'))
                                     .WithPorts(service_component.ports + { 
                                        [port_name]: service_component.sidecars[sidecar_name].ports[port_name]
                                        for sidecar_name in std.objectFields(utils.objectGet(service_component, 'sidecars', {})) 
                                        for port_name in std.objectFields(utils.objectGet(service_component.sidecars[sidecar_name], 'ports', {}))
                                      })
                                     {
    workload:: error 'Workload must be set',
    target_pod:: self.workload.spec.template,
  },

  StatefulSet(name, service_component, config_map_configs, secrets_configs)::
    local main_container = $.Container(service_component.name, service_component, config_map_configs, secrets_configs);
    local additional_containers = {
      local container = service_component.sidecars[container_name],
      [container_name]: $.Container(container_name, container, config_map_configs, secrets_configs)
      for container_name in std.objectFields(utils.objectGet(service_component, 'sidecars', {}))
    };
    kap.K8sStatefulSet(name)
    .WithPodAntiAffinity(name, 'kubernetes.io/hostname', utils.objectGet(service_component, 'prefer_pods_in_different_nodes', false))
    .WithNamespace()
    .WithAnnotations(utils.objectGet(service_component, 'annotations', {}))
    .WithContainer({ default: main_container } + additional_containers )
    .WithDNSPolicy(utils.objectGet(service_component, 'dns_policy'))
    .WithLabels(utils.objectGet(service_component, 'labels', {}))
    .WithSecurityContext(utils.objectGet(service_component, 'workload_security_context', {}))
    .WithMinReadySeconds(utils.objectGet(service_component, 'min_ready_seconds'))
    .WithNamespace(kap.parameters.namespace)
    .WithProgressDeadlineSeconds(utils.objectGet(service_component, 'deployment_progress_deadline_seconds'))
    .WithPrometheusScrapeAnnotation(utils.objectGet(service_component, 'enable_prometheus', false), utils.objectGet(service_component, 'prometheus_port', 6060))
    .WithReplicas(utils.objectGet(service_component, 'replicas', 1))
    .WithRestartPolicy(utils.objectGet(service_component, 'restart_policy', 'Always'))
    .WithUpdateStrategy(utils.objectGet(service_component, 'update_strategy', {}))
    .WithServiceAccountName(utils.objectGet(service_component, 'service_account', {}))
    .WithVolume(utils.objectGet(service_component, 'volumes', {}))
    .WithVolume({ [config_map_name]: $.ConfigVolume(config_map_configs[config_map_name].manifest, config_map_configs[config_map_name].config.items) for config_map_name in std.objectFields(config_map_configs) }, config_map_configs != null)
    .WithVolume({ [secret_name]: $.SecretVolume(secrets_configs[secret_name].manifest, utils.objectGet(secrets_configs[secret_name].config, 'items', [])) for secret_name in std.objectFields(secrets_configs) }, secrets_configs != null)
    .WithVolumeClaimTemplates(utils.objectGet(service_component, 'volume_claims', {}))

  ,
  Deployment(name, service_component, config_map_configs, secrets_configs)::
    local main_container = $.Container(service_component.name, service_component, config_map_configs, secrets_configs);
    local additional_containers = {
      local container = service_component.sidecars[container_name],
      [container_name]: $.Container(container_name, container, config_map_configs, secrets_configs)
      for container_name in std.objectFields(utils.objectGet(service_component, 'sidecars', {}))
    };

    kap.K8sDeployment(name)
    .WithPodAntiAffinity(name, 'kubernetes.io/hostname', utils.objectGet(service_component, 'prefer_pods_in_different_nodes', false))
    .WithPodAntiAffinity(name, 'failure-domain.beta.kubernetes.io/zone', utils.objectGet(service_component, 'prefer_pods_in_different_zones', false))
    .WithNodeAffinity('synthace.com/node-type', utils.objectGet(service_component, 'prefer_pods_in_node_type', 'standard'), 'In', utils.objectHas(service_component, 'prefer_pods_in_node_type', false))
    .WithNodeSelector(utils.objectGet(service_component, 'node_selector_labels', {}))
    .WithNamespace()
    .WithAnnotations(utils.objectGet(service_component, 'annotations', {}))
    .WithContainer({ default: main_container } + additional_containers)
    .WithSecurityContext(utils.objectGet(service_component, 'workload_security_context', {}))
    .WithDNSPolicy(utils.objectGet(service_component, 'dns_policy'))
    .WithLabels(utils.objectGet(service_component, 'labels', {}))
    .WithMinReadySeconds(utils.objectGet(service_component, 'min_ready_seconds'))
    .WithProgressDeadlineSeconds(utils.objectGet(service_component, 'deployment_progress_deadline_seconds'))
    .WithPrometheusScrapeAnnotation(utils.objectGet(service_component, 'enable_prometheus', false), utils.objectGet(service_component, 'prometheus_port', 6060))
    .WithReplicas(utils.objectGet(service_component, 'replicas', 1))
    .WithRestartPolicy(utils.objectGet(service_component, 'restart_policy', 'Always'))
    .WithUpdateStrategy(utils.objectGet(service_component, 'update_strategy', {}))
    .WithServiceAccountName(utils.objectGet(service_component, 'service_account', {}))
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
    local has_cluster_role = utils.objectHas(service_component, 'cluster_role', false);
    local has_webhooks = utils.objectHas(service_component, 'webhooks', false);
    local has_service_monitor = utils.objectHas(service_component, 'service_monitors', false);
    local has_prometheus_rule = utils.objectHas(service_component, 'prometheus_rules', false);




    local config_helpers = {
      local global_annotations = utils.objectGet(service_component, 'globals', {}),
      secrets: {
        config: utils.objectGet(service_component, 'secrets', {}),
        global_annotations: utils.objectGet(global_annotations, 'secrets', {}),
        generating_class: kap.K8sSecret
      },
      migration_secrets: {
        config: utils.deepMerge(config_helpers.secrets.config, utils.objectGet(service_component.migration, 'secrets', {})),
        global_annotations: utils.objectGet(global_annotations, 'secrets', {}),
        generating_class: kap.K8sSecret
      },
      config_maps: {
        config: utils.objectGet(service_component, 'config_maps', {}),
        global_annotations: utils.objectGet(global_annotations, 'config_maps', {}),
        generating_class: kap.K8sConfigMap
      }
    };

    local MergeConfig(name, helper) = {
      name:: if std.length(helper.config) == 1 then service_component.name else '%s-%s' % [service_component.name, name],
      manifest: helper.generating_class(self.name, utils.objectGet(helper.config[name], 'data', {}))
                  .WithAnnotations(utils.objectGet(helper.global_annotations, 'annotations', {}))
                  .WithAnnotations(utils.objectGet(helper.config[name], 'annotations', {}))
                  .WithLabels(utils.objectGet(helper.global_annotations, 'labels', {}))
                  .WithLabels(utils.objectGet(helper.config[name], 'labels', {}))
                  .WithNamespace(),
      config: {items: []} + helper.config[name],
    };

    local CreateConfigDefinition(helper) = {
      [name]: MergeConfig(name, helper)
      for name in std.objectFields(helper.config)
    };

    local objects = {
      [name]: CreateConfigDefinition(config_helpers[name])
        for name in std.objectFields(config_helpers)
    };

    local secrets_manifests = [secret.manifest for secret in utils.objectValues(objects.secrets)];
    local config_map_manifests = [config_map.manifest for config_map in utils.objectValues(objects.config_maps)];




    local workload_type = utils.objectGet(service_component, 'type', 'deployment');
    local workload = if workload_type == 'deployment' then
      $.Deployment(service_component.name, service_component, objects.config_maps, objects.secrets)
    else if workload_type == 'statefulset' then
      $.StatefulSet(service_component.name, service_component, objects.config_maps, objects.secrets);
    local service = if has_service then $.Service(service_component.name, service_component).WithNamespace() + { workload:: workload };


    local sa = utils.objectGet(service_component, 'service_account');
    local sa_name = utils.objectGet(sa, 'name', service_component.name);
    local serviceAccount = if utils.objectGet(sa, 'create', false) then kap.K8sServiceAccount(sa_name)
      .WithNamespace()
      .WithAnnotations(utils.objectGet(sa, 'annotations', {})) else {}
    ;
    local cr = if has_cluster_role then utils.objectGet(service_component, 'cluster_role');
    local cr_name = sa_name;
    local clusterRole =  if has_cluster_role then kap.K8sClusterRole(cr_name)
        .WithRules(utils.objectGet(cr, 'rules'))
        .WithLabels(utils.objectGet(service_component, 'labels', {}))
    ;
    local cr_binding = if has_cluster_role then utils.objectGet(cr, 'binding');
    local clusterRoleBinding =  if has_cluster_role then kap.K8sClusterRoleBinding(cr_name)
    .WithSubjects(utils.objectGet(cr_binding, 'subjects'))
    .WithRoleRef(utils.objectGet(cr_binding, 'roleRef'))
    .WithLabels(utils.objectGet(service_component, 'labels', {}))
    ;


    local webhooks = if has_webhooks then kap.K8sMutatingWebhookConfiguration(service_component.name)
      .withWebHooks(utils.objectGet(service_component, 'webhooks', []));

    local service_monitor = if has_service_monitor then utils.objectGet(service_component, 'service_monitors');
    local service_monitors = if has_service_monitor then prom.ServiceMonitor(service_component.name + '-metrics')
      .WithNamespace()
      .WithEndPoints(utils.objectGet(service_monitor, 'endpoints', []))
      .WithSelector(utils.objectGet(service_monitor, 'selector', { matchLabels: { name: service_component.name }}))
      .WithNameSpaceSelector(utils.objectGet(service_monitor, 'namespace_selector',  { matchNames: [ p.namespace ] }))
      ;

    local prometheus_rule = if has_prometheus_rule then utils.objectGet(service_component, 'prometheus_rules');
    local prometheus_rules = if has_prometheus_rule then prom.PrometheusRule(service_component.name + '.rules')
      .WithNamespace()
      .WithRules(utils.objectGet(prometheus_rule, 'rules', []))
      ;

    local vpa_mode=utils.objectGet(service_component, 'vpa', 'Auto');
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
        minAvailable: utils.objectGet(service_component, 'pdb_min_available')
      } ,
      metadata+: {
        namespace: p.namespace
      }
    };


    $.Bundle()
    .WithItem('config', config_map_manifests, has_configmaps)
    .WithItem('secret', secrets_manifests, has_secrets)
    .WithItem('sa', serviceAccount)
    .WithBundled('workload', workload)
    .WithBundled('vpa', vpa, utils.objectHas(service_component, 'vpa', false))
    .WithBundled('pdb', pdb, utils.objectHas(service_component, 'pdb_min_available'))
    .WithBundled('service', service)
    .WithBundled('webhooks', webhooks)
    .WithBundled('service_monitors', service_monitors)
    .WithBundled('prometheus_rules', prometheus_rules)
    .WithBundled('cr', clusterRole)
    .WithBundled('crb', clusterRoleBinding),
}
