# Copyright (c) 2023 All Rights Reserved
# Generated code

import hashlib
import random
from dtm import Role, Person, Ad
import sys

def recommend_events(args):
    user = args['user']
    subscriptions = user.subscriptions
    attending = user.attends
    events = [event for category in subscriptions for event in category.events]
    return list(set(events) - set(attending)) 

def get_personalize_ad(args):
    user = args['user']
    seed_string = f"{user.id}{user.name}{user.gender}"
    seed_value = int(hashlib.sha256(seed_string.encode()).hexdigest(), 16)
    random.seed(seed_value)
    ads = Ad.query.all()
    if len(ads) == 0:
        return None
    else:
        return ads[random.randint(1, len(ads)) - 1]

def send_advertisement_to_user(args):
    user = args['user']
    if user.email:
        print(f'A generic advertisement was sent to {user.name} at email: {user.email}.', file=sys.stderr)

def get_candidates(args):
    cat = args['cat']
    all_ids = [m.id for m in Person.query.all() if Role.MODERATOR == m.role]
    mod_ids = [m.id for m in cat.moderators]
    candidate_ids = list(set(all_ids) - set(mod_ids)) 
    return [Person.query.get(id) for id in candidate_ids]


























