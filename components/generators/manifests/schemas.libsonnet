{
  service_component: {
    type: 'object',
    title: 'manifest generator',
    description: 'Schema for Kapitan manifest generator',
    required: ['name', 'image', 'type'],
    additionalProperties: false,
    properties: {
      application: {
        description: 'Associates this component to an application.',
        type: 'string',
      },
      annotations: {
        description: 'Annotations to pass to the workload',
        type: 'object',
        additionalProperties: { type: 'string' },
      },
      args: {
        description: 'Args to pass to the workload',
        type: 'array',
        items: { type: 'string' },
      },
      command: {
        description: 'command to pass to the workload',
        type: 'array',
        items: { type: 'string' },
      },
      config_maps: {
        description: 'Config maps for the workload',
        anyOf: [{ type: 'null' }, {
          type: 'object',
          additionalProperties: { '$ref': '#/definitions/config' },
        }],
      },
      deployment_progress_deadline_seconds: { anyOf: [{ type: 'null' }, { type: 'integer' }] },
      dns_policy: { type: 'string', enum: ['ClusterFirst'] },
      pull_policy: { type: 'string', enum: ['Always', 'IfNotPresent'] },
      vpa: { type: 'string', enum: ['Off', 'Auto'] },
      enable_prometheus: { type: 'boolean' },
      enabled: { type: 'boolean' },
      pdb_min_available: { type: 'integer' },
      env: { anyOf: [{ type: 'null' }, { type: 'object' }] },
      resources: {
        type: 'object',
        properties: {
          limits: {
            anyOf: [{ type: 'null' }, {
              type: 'object',
              properties: {
                cpu: { type: 'string' },
                memory: { type: 'string' },
                additionalProperties: true,
              },
            }],
          },
          requests: {
            anyOf: [{ type: 'null' }, {
              type: 'object',
              properties: {
                cpu: { type: 'string' },
                memory: { type: 'string' },
                additionalProperties: true,
              },
            }],
          },
        },
        additionalProperties: false,
      },
      cluster_role: { anyOf: [{ type: 'null' }, { type: 'object' }] },
      additional_containers: { anyOf: [{ type: 'null' }, { type: 'object' }] },
      healthcheck: {
        type: 'object',
        properties: {
          readiness: {
            anyOf: [{ type: 'null' }, {
              type: 'object',
              properties: {
                type: { type: 'string', enum: ['command', 'http', 'tcp'] },
                timeout_seconds: { type: 'integer' },
                initial_delay_seconds: { type: 'integer' },
                failure_threshold: { type: 'integer' },
                success_threshold: { type: 'integer' },
                period_seconds: { type: 'integer' },
                enabled: { type: 'boolean' },
                httpHeaders: {
                  type: 'array',
                  items: { type: 'object' },
                },
                path: { type: 'string' },
                scheme: { type: 'string', enum: ['HTTP', 'HTTPS'] },
                port: {
                  oneOf: [
                    { type: 'string' },
                    { type: 'integer' },
                  ],
                },
                command: {
                  type: 'array',
                  items: { type: 'string' },
                },
              },
            }],
          },
          liveness: {
            anyOf: [{ type: 'null' }, {
              type: 'object',
              properties: {
                type: { type: 'string', enum: ['command', 'http', 'tcp'] },
                timeout_seconds: { type: 'integer' },
                initial_delay_seconds: { type: 'integer' },
                failure_threshold: { type: 'integer' },
                success_threshold: { type: 'integer' },
                period_seconds: { type: 'integer' },
                enabled: { type: 'boolean' },
                httpHeaders: {
                  type: 'array',
                  items: { type: 'object' },
                },
                path: { type: 'string' },
                scheme: { type: 'string', enum: ['HTTP', 'HTTPS'] },
                port: {
                  oneOf: [
                    { type: 'string' },
                    { type: 'integer' },
                  ],
                },
                command: {
                  type: 'array',
                  items: { type: 'string' },
                },
              },
            }],
          },
        },
        additionalProperties: false,
      },
      image: { type: 'string' },
      labels: { type: 'object', additionalProperties: { type: 'string' } },
      name: { type: 'string' },
      node_selector_labels: { type: 'object' },
      network_policies: { type: 'object' },
      service_account: {
        anyOf: [{ type: 'null' }, {
          type: 'object',
          properties: {
            name: { type: 'string' },
            create: { type: 'boolean' },
            enabled: { type: 'boolean' },
            annotations: { anyOf: [{ type: 'null' }, { type: 'object', additionalValues: { type: 'string' } }] },
          },
          additionalProperties: false,
        }],
      },
      update_strategy: { type: 'object' },
      security_context: { type: 'object' },
      workload_security_context: { type: 'object' },
      min_ready_seconds: { type: 'integer' },
      ports: {
        type: 'object',
        additionalProperties: { '$ref': '#/definitions/port_set' },
      },
      globals: {
        anyOf: [{ type: 'null' }, {
          type: 'object',
          properties: {
            secrets: { type: 'object', additionalProperties: { '$ref': '#/definitions/globals' } },
            config_maps: { type: 'object', additionalProperties: { '$ref': '#/definitions/globals' } },
          },
          additionalProperties: false,
        }],
      },
      secrets: { anyOf: [{ type: 'null' }, {
        type: 'object',
        additionalProperties: { '$ref': '#/definitions/secret' },
      }] },
      security: { anyOf: [{ type: 'null' }, {
        type: 'object',
        properties: {
          allow_privilege_escalation: { type: 'boolean' },
          user_id: { type: 'integer' },
        },
        additionalProperties: false,
      }] },
      service: {
        type: 'object',
        properties: {
          annotations: { type: 'object', additionalValues: { type: 'string' } },
          externalTrafficPolicy: { type: 'string', enum: ['Cluster'] },
          grpc: { type: 'object' },
          type: { type: 'string', enum: ['NodePort', 'ClusterIP', 'LoadBalancer'] },
        },
        additionalProperties: false,
      },
      webhooks: { type: 'array', items: { type: 'object' } },
      service_monitors: { type: 'object', items: { type: 'object' } },
      prometheus_rules: { type: 'object', items: { type: 'object' } },
      replicas: { type: 'integer' },
      prefer_pods_in_different_nodes: { type: 'boolean' },
      prefer_pods_in_different_zones: { type: 'boolean' },
      prefer_pods_in_node_type: { type: 'string' },
      type: { type: 'string', enum: ['statefulset', 'deployment'] },
      volume_claims: { type: 'object', additionalProperties: { '$ref': '#/definitions/volume_claim' } },
      volume_mounts: { type: 'object', additionalProperties: { type: 'object' } },
      volumes: { type: 'object', additionalProperties: { type: 'object' } },

    },
    definitions: {
      volume_claim: {
        type: 'object',
        properties: {
          spec: { type: 'object' },
        },
      },
      config: {
        type: 'object',
        properties: {
          data: {
            type: 'object',
            additionalProperties: {
              type: 'object',
              properties: {
                value: { type: 'string' },
                values: { type: 'object' },
                template: { type: 'string' },
                b64_encode: { type: 'boolean' },
              },
              additionalProperties: false,
            },
          },
          items: { type: 'array', items: { type: 'string' } },
          mount: { type: 'string' },
          annotations: { anyOf: [{ type: 'null' }, { type: 'object', additionalValues: { type: 'string' } }] },
        },
        required: ['data'],
      },
      globals: {
        type: 'object',
        properties: {
          annotations: { anyOf: [{ type: 'null' }, { type: 'object', additionalValues: { type: 'string' } }] },
          labels: { anyOf: [{ type: 'null' }, { type: 'object', additionalValues: { type: 'string' } }] },
        },
      },
      secret: {
        type: 'object',
        properties: {
          data: {
            type: 'object',
            additionalProperties: {
              type: 'object',
              properties: {
                value: { type: 'string' },
                values: { type: 'object' },
                template: { type: 'string' },
                b64_encode: { type: 'boolean' },
              },
              additionalProperties: false,
            },
          },
          items: { type: 'array', items: { type: 'string' } },
          mount: { type: 'string' },
          annotations: { anyOf: [{ type: 'null' }, { type: 'object', additionalValues: { type: 'string' } }] },
        },
        required: ['data'],
      },
      kube_env: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            name: { type: 'string' },
            value: { type: 'string' },
            valueFrom: {
              anyOf: [
                {
                  type: 'object',
                  properties: {
                    secretKeyRef: {
                      type: 'object',
                      properties: {
                        key: { type: 'string' },
                        optional: { type: 'boolean' },
                      },
                      additionalProperties: false,
                      required: ['key'],
                    },
                  },
                  required: ['secretKeyRef'],
                  additionalProperties: false,
                },
                {
                  type: 'object',
                  properties: {
                    fieldRef: {
                      type: 'object',
                      properties: {
                        fieldPath: { type: 'string' },
                      },
                      required: ['fieldPath'],
                      additionalProperties: false,
                    },
                  },
                  required: ['fieldRef'],
                  additionalProperties: false,
                },
              ],
            },
          },
          additionalProperties: false,
          required: ['name'],
        },
      },
      port_set: {
        type: 'object',
        properties: {
          container_port: { type: 'integer' },
          node_port: { type: 'integer' },
          service_port: { type: 'integer' },
          protocol: { type: 'string', enum: ['UDP', 'TCP'] },
        },
        additionalProperties: false,
      },
    },
  },
}
