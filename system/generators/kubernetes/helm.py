import logging

logger = logging.getLogger(__name__)

from typing import Any

from kapitan.inputs.helm import HelmChart
from kapitan.inputs.kadet import BaseObj

from .common import KubernetesResource, kgenlib


class MyHelmChart(HelmChart):
    def new(self):
        for obj in self.load_chart():
            if obj:
                self.root[
                    f"{obj['metadata']['name'].lower()}-{obj['kind'].lower().replace(':','-')}"
                ] = BaseObj.from_dict(obj)


@kgenlib.register_generator(path="charts")
class HelmChartGenerator(kgenlib.BaseStore):
    name: str
    config: Any

    def body(self):
        helm_config = self.config.to_dict()
        chart_name = self.config.helm_params.name

        rendered_chart = MyHelmChart(**helm_config)

        for helm_resource in rendered_chart.root.values():
            resource = KubernetesResource.from_baseobj(helm_resource)
            resource.add_label("app.kapicorp.dev/component", chart_name)
            self.add(resource)
