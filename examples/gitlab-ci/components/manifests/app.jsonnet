local kap = import "lib/kapitan.libjsonnet";
local inv = kap.inventory();
local app = inv.parameters.app;

local labels = { app: app.name };

{
  deployment: {
    apiVersion: "apps/v1",
    kind: "Deployment",
    metadata: {
      name: app.name,
      namespace: app.namespace,
      labels: labels,
    },
    spec: {
      replicas: app.replicas,
      selector: { matchLabels: labels },
      template: {
        metadata: { labels: labels },
        spec: {
          containers: [
            {
              name: app.name,
              image: app.image,
              ports: [{ containerPort: app.port }],
            },
          ],
        },
      },
    },
  },
  service: {
    apiVersion: "v1",
    kind: "Service",
    metadata: {
      name: app.name,
      namespace: app.namespace,
      labels: labels,
    },
    spec: {
      selector: labels,
      ports: [{ port: app.port, targetPort: app.port }],
    },
  },
}
