{% set p = inventory.parameters %}
# {{p.target_name}}

|||
| --- | --- |
| **Target** | {{ p.target_name }} |
| **Project**     | `{{p.google_project | default('not defined')}}`|
| **Cluster**     | {% if p.cluster is defined %} {{p.cluster.name }} {% else %} 'Not defined' {% endif %} |
| **Namespace**   | `{{p.namespace}}` |

{% if p.components is defined %}
## Components
| Inventory definition | Documentation |
| --- | --- |
{% for component in p.components|sort %}
|[{{component}}.yml](../../inventory/classes/components/{{component}}.yml)| [{{component}}]({{component}}-readme.md)|
{% endfor %}
{% endif %}

## Deployments

