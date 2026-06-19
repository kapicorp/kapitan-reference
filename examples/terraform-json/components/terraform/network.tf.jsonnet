local kap = import "lib/kapitan.libjsonnet";
local inv = kap.inventory();
local tf = inv.parameters.terraform;

local zones = tf.network.zones;

// One subnet per zone, addressed from the environment's CIDR prefix.
local subnets = {
  [zones[i]]: {
    name: "%s-%s" % [tf.network.name, zones[i]],
    cidr_block: "%s.%d.0/24" % [tf.network.cidr_prefix, i],
  }
  for i in std.range(0, std.length(zones) - 1)
};

{
  // Key becomes the file name; output_type json writes network.tf.json.
  "network.tf": {
    terraform: {
      required_version: ">= 1.4",
    },
    variable: {
      environment: {
        type: "string",
        default: tf.environment,
      },
    },
    locals: {
      network_name: tf.network.name,
      region: tf.region,
    },
    resource: {
      // terraform_data is a built-in resource, so the output validates
      // without any cloud provider. Swap it for real provider resources
      // (google_compute_subnetwork, aws_subnet, ...) for actual infra.
      terraform_data: {
        ["subnet_" + zone]: {
          input: subnets[zone],
        }
        for zone in zones
      },
    },
    output: {
      subnets: {
        value: subnets,
      },
    },
  },
}
