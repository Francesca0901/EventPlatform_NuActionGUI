# Copyright (c) 2023 All Rights Reserved
# Generated code
from instrumentation import secure
from dtm import db
from app import P












@secure(db,P(['RECOMMENDEVENTS']))
def recommend_events(args):
    from project_aux import recommend_events 
    return recommend_events(args)


@secure(db,P(['MASSMARKETING']))
def send_advertisement_to_user(args):
    from project_aux import send_advertisement_to_user 
    return send_advertisement_to_user(args)





















@secure(db,P([]))
def get_candidates(args):
    from project_aux import get_candidates 
    return get_candidates(args)





@secure(db,P(['TARGETEDMARKETING', 'CORE']))
def get_personalize_ad(args):
    from project_aux import get_personalize_ad 
    return get_personalize_ad(args)

