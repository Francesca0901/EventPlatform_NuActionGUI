# Copyright (c) 2023 All Rights Reserved
# Generated code
from instrumentation import secure
from dtm import db
from app import P

{% for c in dm if not c.isAssociation %}
{%- for m in c.methods %}
{%- if not m.entry %}
@secure(db,P({{- get_purpose(m.name)}}))
def {{m.name}}(args):
    from project_aux import {{m.name}} 
    return {{m.name}}(args)
{% endif %}
{% endfor %}
{%- endfor %}