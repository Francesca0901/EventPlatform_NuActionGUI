from model import Action, Constraint
from enum import auto, Enum
from privacy_model import PrivacyModel
import dtm

class {{projectname}}PrivacyModel(PrivacyModel):

    # Extensible model (default: nothing declared)

    class Purpose(Enum):
        {% if pm.purposes|length == 0 %}
        pass
        {% else %}
        {% for p in pm.purposes -%}
        {{ p.name }} = auto()
        {% endfor %}
        {% endif %}

    personaldata = [
        {% for p in pm.personalData -%}
        {{ p }}{% if not loop.last %},{% endif %}
        {% endfor -%}
    ]
        
    model = {{policy | replace('\'Action.read\'','Action.read') |
                        replace('\'Action.add\'','Action.add') |
                        replace('\'Action.remove\'','Action.remove') |
                        replace('\'Action.update\'','Action.update') |
                        replace('\'Action.create\'','Action.create') |
                        replace('\'Action.delete\'','Action.delete') |
                        replace('\'Constraint.fullAccess\'','Constraint.fullAccess') | 
                        replace('\'Constraint.noAccess\'','Constraint.noAccess') | 
                        r | rrr }}

{{projectname}}PrivacyModel.validate()