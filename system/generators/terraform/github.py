import logging

logger = logging.getLogger(__name__)

from .common import TerraformResource, TerraformStore, kgenlib


@kgenlib.register_generator(
    path="terraform.gen_github_repository",
    apply_patches=["generators.terraform.defaults.gen_github_repository"],
)
class GenGitHubRepository(TerraformStore):
    def body(self):
        resource_id = self.id
        config = self.config

        branch_protection_config = config.pop("branch_protection", {})
        deploy_keys_config = config.pop("deploy_keys", {})

        resource_name = self.name
        logging.debug(f"Processing github_repository {resource_name}")
        repository = TerraformResource(
            id=resource_id,
            type="github_repository",
            config=config,
            defaults=self.defaults,
        )
        repository.set(config)
        repository.filename = "github_repository.tf"

        self.add(repository)

        for branches_name, branches_config in branch_protection_config.items():
            logger.debug(f"Processing branch protection for {branches_name}")
            branch_protection = TerraformResource(
                id=f"{resource_id}_{branches_name}",
                type="github_branch_protection",
                config=branches_config,
                defaults=self.defaults,
            )
            branch_protection.filename = "github_branch_protection.tf"
            branch_protection.set(branch_protection.config)
            branch_protection.add("repository_id", repository.get_reference("node_id"))
            self.add(branch_protection)

        for deploy_key_name, deploy_key_branches in deploy_keys_config.items():
            logger.debug(f"Processing deploy keys for {deploy_key_name}")
            deploy_key = TerraformResource(
                id=f"{resource_id}_{deploy_key_name}",
                type="github_repository_deploy_key",
                config=deploy_key_branches,
                defaults=self.defaults,
            )
            deploy_key.filename = "github_deploy_key.tf"
            deploy_key.set(deploy_key.config)
            deploy_key.add("repository", repository.get_reference("name"))
            self.add(deploy_key)
