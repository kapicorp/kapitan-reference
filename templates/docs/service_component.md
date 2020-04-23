# Documentation for {{service_component.name}} on {{inventory.target_name}}

|||
| --- | ---- |
| **Component name** | {{service_component.name}} |
| **Application** | {{service_component.application | default('Not Defined')}} |
| **Replicas** | {{service_component.replicas | default('1')}} |
| **Image** | {{service_component.image}} |

{% if service_component.env is defined %}
| ENV | VALUE |
| --- | -----  |
{% for env in service_component.env  %}
{% set env_value = service_component.env[env] %}
{% if env_value is mapping %}
{% if env_value.secretKeyRef is defined %}
|{{env}} | taken from secret with key: ``{{env_value.secretKeyRef.key}}``|
{% else  %}
|{{env}} | UNMATCHED {{env_value}}|
{% endif %}
{% else %}
|{{env}} | {{env_value}}|
{% endif %}
{% endfor %}
{% endif %}
