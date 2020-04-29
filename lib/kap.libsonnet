/*
 * This class hides all the boilerplate needed for kapitan.
 */

local kapitan = import 'lib/kapitan.libjsonnet';
local kube = import 'lib/kube.libsonnet';
local utils = import 'lib/utils.libsonnet';

local inventory = kapitan.inventory();
local p = inventory.parameters;

local isRefTag = function(potential_ref_tag)
  std.startsWith(potential_ref_tag, '?{') && std.endsWith(potential_ref_tag, '}')
;

local getFilePathFromRef = function(ref_tag)
  // Remove the leading `?{` and the trailing `}`
  local ref_content = std.substr(ref_tag, 2, std.length(ref_tag) - 3);
  // Remove the scheme (e.g., `gkms:`, `plain:`)
  local ref_content_without_scheme = std.splitLimit(ref_content, ':', 1)[1];
  // Remove any pipelines
  std.splitLimit(ref_content_without_scheme, '|', 1)[0]
;

local loadRefFile = function(potential_ref_tag)
  local final_file_path = 'refs/' + getFilePathFromRef(potential_ref_tag);
  kapitan.file_read(final_file_path)
;

local version_secrets = utils.objectGet(p, 'version_secrets', false);

local HealthCheck = function(healthcheck_config) if utils.objectGet(healthcheck_config, 'enabled', true) then {
  failureThreshold: 3,
  periodSeconds: 10,
  successThreshold: 1,
  timeoutSeconds: utils.objectGet(healthcheck_config, 'timeout_seconds', 1),
  [if healthcheck_config.type == 'command' then 'exec']: {
    command: healthcheck_config.command,
  },
  [if healthcheck_config.type == 'http' then 'httpGet']: {
    path: healthcheck_config.path,
    port: utils.objectGet(healthcheck_config, 'port', 80),
    scheme: utils.objectGet(healthcheck_config, 'scheme', 'HTTP'),
  },
  [if healthcheck_config.type == 'tcp' then 'tcpSocket']: {
    port: utils.objectGet(healthcheck_config, 'port', 80),
  },
};

kapitan + kube + {
  inventory: inventory,
  parameters: inventory.parameters,
  utils: utils,
  kapitan: kapitan,


  AntiAffinityPreferred(name, topology_key): {
    spec+: {
      template+: {
        spec+: {
          affinity+: {
            podAntiAffinity+: {
              preferredDuringSchedulingIgnoredDuringExecution+: [{
                weight: 1,
                podAffinityTerm: {
                  labelSelector: {
                    matchExpressions: [{
                      key: 'app',
                      operator: 'In',
                      values: [name],
                    }],
                  },
                  topologyKey: topology_key,
                },
              }],
            },
          },
        },
      },
    },
  },
  NodeAffinityPreferred(label, value, operator='In'): {
    spec+: {
      template+: {
        spec+: {
          affinity+: {
            nodeAffinity+: {
              preferredDuringSchedulingIgnoredDuringExecution+: [{
                weight: 1,
                preference: {
                  matchExpressions: [{
                    key: label,
                    operator: operator,
                    values: [value],
                  }],
                },
              }],
            },
          },
        },
      },
    },
  },

  K8sCommon(name): {
    WithAnnotations(annotations):: self + { metadata+: { annotations+: annotations } },
    WithLabels(labels):: self + { metadata+: { labels: labels } },
    WithLabel(label):: self + { metadata+: { labels+: label } },
    WithTemplateLabel(label):: self + { spec+: { template+: { metadata+: { labels+: label } } } },
    WithMetadata(metadata):: self + { metadata+: metadata },
    WithNamespace(namespace=p.namespace):: self + { metadata+: { namespace: namespace } },
  },
  K8sService(name): $.K8sCommon(name) + kube.Service(name) {
    WithExternalTrafficPolicy(policy):: self + { spec+: { externalTrafficPolicy: policy } },
    WithType(type):: self + { spec+: { type: type } },
    WithSessionAffinity(affinity):: self + { spec+: { sessionAffinity: affinity } },
    WithPorts(ports):: self + { spec+: { ports: [
      {
        port_info:: ports[port_name],
        name: port_name,
        port: self.port_info.service_port,
        protocol: 'TCP',
        nodePort: utils.objectGet(self.port_info, 'node_port'),
        targetPort: port_name,
      }
      for port_name in std.objectFields(ports)
    ] } },
  },
  K8sDeployment(name): $.K8sCommon(name) + kube.Deployment(name) {
    spec+: {
      revisionHistoryLimit: utils.objectGet(p, 'revisionHistoryLimit', null),
    },
    WithPodAntiAffinity(name=name, topology, enabled=true):: self + if enabled then $.AntiAffinityPreferred(name, topology) else {},
    WithNodeAffinity(label, value, operator='In', enabled=true):: self + if enabled then $.NodeAffinityPreferred(label, value, operator) else {},
    WithContainer(container):: self + { spec+: { template+: { spec+: { containers_+: container } } } },
    WithMinReadySeconds(seconds):: self + { spec+: { minReadySeconds: seconds } },
    WithProgressDeadlineSeconds(seconds):: self + { spec+: { progressDeadlineSeconds: seconds } },
    WithReplicas(replicas):: self + { spec+: { replicas: replicas } },
    WithUpdateStrategy(strategy):: self + { spec+: { strategy+: strategy } },
    WithPrometheusScrapeAnnotation(enabled=true, port=6060):: self + if enabled then { spec+: { template+: { metadata+: { annotations+: {
      'prometheus.io/port': std.toString(port),
      'prometheus.io/scrape': std.toString(enabled),
    } } } } } else {},
    WithDNSPolicy(policy):: self + { spec+: { template+: { spec+: { dnsPolicy: policy } } } },
    WithRestartPolicy(policy):: self + { spec+: { template+: { spec+: { restartPolicy: policy } } } },
    WithServiceAccountName(serviceAccountName, enabled):: self + if enabled then { spec+: { template+: { spec+: { serviceAccountName: serviceAccountName } } } } else {},
    WithVolume(volume, enabled=true):: self + if enabled then { spec+: { template+: { spec+: { volumes_+: volume } } } } else {},
  },

  K8sStatefulSet(name): $.K8sCommon(name) + kube.StatefulSet(name) {
    spec+: {
      revisionHistoryLimit: utils.objectGet(p, 'revisionHistoryLimit', null),
    },
    WithPodAntiAffinity(name=name, topology, enabled=true):: self + if enabled then $.AntiAffinityPreferred(name, topology) else {},
    WithContainer(container):: self + { spec+: { template+: { spec+: { containers_+: container } } } },
    WithMinReadySeconds(seconds):: self + { spec+: { minReadySeconds: seconds } },
    WithUpdateStrategy(strategy):: self + { spec+: { updateStrategy+: strategy } },
    WithProgressDeadlineSeconds(seconds):: self + { spec+: { progressDeadlineSeconds: seconds } },
    WithReplicas(replicas):: self + { spec+: { replicas: replicas } },
    WithPrometheusScrapeAnnotation(enabled=true, port=6060):: self + if enabled then { spec+: { template+: { metadata+: { annotations+: {
      'prometheus.io/port': std.toString(port),
      'prometheus.io/scrape': std.toString(enabled),
    } } } } } else {},
    WithDNSPolicy(policy):: self + { spec+: { template+: { spec+: { dnsPolicy: policy } } } },
    WithRestartPolicy(policy):: self + { spec+: { template+: { spec+: { restartPolicy: policy } } } },
    WithServiceAccountName(serviceAccountName, enabled):: self + if enabled then { spec+: { template+: { spec+: { serviceAccountName: serviceAccountName } } } } else {},
    WithVolume(volume, enabled=true):: self + if enabled then { spec+: { template+: { spec+: { volumes_+: volume } } } } else {},
    WithVolumeClaimTemplates(vct, enabled=true):: self + if enabled then { spec+: { volumeClaimTemplates_+: vct } } else {},
  },

  K8sJob(name): $.K8sCommon(name) + kube.Job(name) {
    WithContainer(container):: self + { spec+: { template+: { spec+: { containers_+: container } } } },
    WithBackoffLimit(limit):: self + { spec+: { backoffLimit: limit } },
    WithDNSPolicy(policy):: self + { spec+: { template+: { spec+: { dnsPolicy: policy } } } },
    WithImagePullSecrets(secret):: self + { spec+: { template+: { spec+: { imagePullSecrets+: [{ name: secret }] } } } },
    WithSelector(selector):: self + { spec+: { selector: selector } },
    WithRestartPolicy(policy):: self + { spec+: { template+: { spec+: { restartPolicy: policy } } } },
    WithServiceAccountName(serviceAccountName, enabled):: self + if enabled then { spec+: { template+: { spec+: { serviceAccountName: serviceAccountName } } } } else {},
    WithVolume(volume, enabled=true):: self + if enabled then { spec+: { template+: { spec+: { volumes_+: volume } } } } else {},
  },

  K8sServiceAccount(name): $.K8sCommon(name) + kube.ServiceAccount(name) + {
    WithImagePullSecrets(secrets):: self + { imagePullSecrets+: secrets },
  },

  K8sContainer(name, service_component, secrets_configs): kube.Container(name) {
    WithLivenessProbe(healthchecks, spec):: self + if utils.arrayHas(healthchecks.probes, 'liveness') then { livenessProbe: HealthCheck(spec) } else {},
    WithReadinessProbe(healthchecks, spec):: self + if utils.arrayHas(healthchecks.probes, 'readiness') then { readinessProbe: HealthCheck(spec) } else {},
    WithCommand(command):: self + { command: command },
    WithArgs(args):: self + { args: args },
    WithImage(image):: self + { image_:: image },
    WithEnvs(envs):: self + { env_: envs },
    WithSecurityContext(security_context):: self + { securityContext +: security_context },
    WithMount(mount, enabled=true):: self + if enabled then { volumeMounts_+: mount } else {},
    WithAllowPrivilegeEscalation(bool, enabled=true):: self + if enabled then { securityContext+: { allowPrivilegeEscalation: bool } } else {},
    WithRunAsUser(user, enabled=true):: self + if enabled then { securityContext+: { runAsUser: user } } else {},
    WithPorts(ports):: self + { ports: [
      {
        containerPort: utils.objectGet(ports[port_name], 'container_port', ports[port_name].service_port),
        name: port_name,
        protocol: 'TCP',
      }
      for port_name in std.objectFields(ports)
    ] },
    local container = self,
    image: container.image_,
    env_:: {},
    DetectSecretsInEnvs(env, secret_name, secrets_configs):: {
      [if 'valueFrom' in env then 'valueFrom']+: {
        [if 'secretKeyRef' in env.valueFrom then 'secretKeyRef']+: {
          secret_manifest:: secrets_configs[secret_name].manifest,
          assert secrets_configs != null :
                 'Env var %s in component %s cannot use valueFrom.secretKeyRef because the component does not have a secret' % [
            env.name,
            name,
          ],
          assert !('name' in env.valueFrom.secretKeyRef) : 'Env var %s in %s should not set secretKeyRef.name' % [
            env.name,
            name,
          ],
          name: self.secret_manifest.metadata.name,
        },
      },
    },

    env: if std.length(secrets_configs) > 0
    then
      [
        env + self.DetectSecretsInEnvs(env, secret_name, secrets_configs)
        for secret_name in std.objectFields(secrets_configs)
        for env in std.sort(self.envList(self.env_), keyF=function(x) x.name)
      ]
    else
      std.sort(self.envList(self.env_), keyF=function(x) x.name),
  },

  K8sSecret(name, data): $.K8sCommon(name) + kube.Secret(name) {
    local secret = self,
    local data_resolved = {
      [key]: if isRefTag(secret.data[key]) then loadRefFile(secret.data[key]) else secret.data[key]
      for key in std.objectFields(secret.data)
    },

    data_digest:: std.md5(std.toString(data_resolved)),
    metadata+: {
      name: if version_secrets then '%s-%s' % [name, std.substr(secret.data_digest, 0, 8)] else name,
      annotations+: {
        'sealedsecrets.bitnami.com/managed': 'true',
      },
    },
    short_name:: name,
    data: {
      [key]: if utils.objectGet(data[key], 'b64_encode', false) then
        std.base64(data[key].value)
      else if utils.objectGet(data[key], 'template', false) != false then
        std.base64(kapitan.jinja2_template(data[key].template, utils.objectGet(data[key], 'values', {})))
      else
        data[key].value
      for key in std.objectFields(data)
    },
  },
  K8sConfigMap(name, data): $.K8sCommon(name) + kube.ConfigMap(name) {
    data: {
      [key]: if utils.objectGet(data[key], 'template', false) != false then
        kapitan.jinja2_template(data[key].template, utils.objectGet(data[key], 'values', {}))
      else
        data[key].value
      for key in std.objectFields(data)
    },
  },
  K8sIngress(name): $.K8sCommon(name) + kube.Ingress(name) {
    spec+: { rules+: []},
    WithDefaultBackend(backend):: self + { spec+: { backend: backend }},
    WithRules(rules):: self + { spec+: { rules+: rules }},
    WithPaths(paths):: self + { spec+: { rules+: [ { http+: { paths+: paths } }] }},
  },
}
