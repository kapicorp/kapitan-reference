import logging

logger = logging.getLogger(__name__)

from .common import (
    TerraformBlock,
    TerraformData,
    TerraformLocal,
    TerraformProvider,
    TerraformResource,
    TerraformStore,
    kgenlib,
)


@kgenlib.register_generator(path="terraform.gen_backend")
class Backend(TerraformBlock):
    block_type = "terraform"
    type = "backend"

    def body(self):
        config = self.config

        self.resource.bucket = config.get("bucket")
        self.resource.prefix = config.get("prefix")
        self.filename = "terraform.tf"


@kgenlib.register_generator(path="terraform.gen_required_providers")
class RequiredProvider(TerraformBlock):
    block_type = "terraform"
    type = "required_providers"

    def body(self):
        config = self.config

        self.set(config)
        self.filename = "terraform.tf"


@kgenlib.register_generator(path="terraform.gen_provider")
class Provider(TerraformStore):
    def body(self):
        id = self.id
        config = self.config

        provider = TerraformProvider(id=id, config=config)
        provider.set(config)

        self.add(provider)


@kgenlib.register_generator(path="terraform.gen_locals")
class Local(TerraformStore):
    def body(self):
        import base64

        id = self.id
        config = self.config
        logger.debug(f"Adding local {id} with config {config}")

        value = config.get("value")

        # Handle support for Kapitan gkms secrets
        if value.startswith("?{gkms:"):
            local = TerraformLocal(id=id)
            reference = f"{id}_reference"
            local.set_local(name=reference, value=value)

            data = f"{id}_data"
            # Split the reference on the : and take the second element (the base64 encoded data)
            local.set_local(
                name=data,
                value=f'${{yamldecode(base64decode(element(split(":", local.{reference}), 1)))}}',
            )

            # Create the google_kms_secret data source
            gkms = TerraformData(id=id, type="google_kms_secret")
            gkms.add("ciphertext", f"${{local.{data}.data}}")
            gkms.add("crypto_key", f"${{local.{data}.key}}")
            self.add(gkms)

            # Create the local conditional on the data being base64 encoded or not
            local.set_local(
                name=id,
                value=f'${{local.{data}.data == "base64" ? base64decode(data.google_kms_secret.{id}.plaintext) : data.google_kms_secret.{id}.plaintext}}',
            )

            self.add(local)

        else:
            local = TerraformLocal(id=id, config=config)
            self.add(local)


@kgenlib.register_generator(path="terraform.data_sources")
class TerraformDataSource(TerraformStore):
    def body(self):
        data_source_type = self.name
        data_sources_sets = self.config

        for data_source_id, data_source_config in data_sources_sets.items():
            data_block = TerraformData(
                id=data_source_id,
                type=data_source_type,
                config=data_source_config,
                defaults=self.defaults,
            )
            data_block.set(data_source_config)

            self.add(data_block)


@kgenlib.register_generator(path="terraform.resources.generic")
class TerraformGenericResource(TerraformStore):
    def body(self):
        resource_type = self.name
        resource_sets = self.config

        for resource_id, resource_config in resource_sets.items():
            resource = TerraformResource(
                id=resource_id,
                type=resource_type,
                config=resource_config,
                defaults=self.defaults,
            )
            resource.set(resource_config)

            self.add(resource)
