from flask import request
from flask_user import current_user, login_required, roles_accepted
from model import db, Person, Role, Event, Category, Purpose, Ad, AnyPurpose, FunctionalPurpose, MarketingPurpose, AnalyticsPurpose, CorePurpose, RecommendEventsPurpose, TargetedMarketingPurpose, MassMarketingPurpose
from dto import PersonDTO, EventDTO, CategoryDTO, RoleDTO, AdDTO, RESTRICTED
import hashlib
import random
import sys

PURPOSES = [
    AnyPurpose, 
    FunctionalPurpose, 
    MarketingPurpose, 
    AnalyticsPurpose, 
    CorePurpose, 
    RecommendEventsPurpose, 
    TargetedMarketingPurpose, 
    MassMarketingPurpose
]


"""
Define your privacy input here. 
We introduce the privacy policy in the following structure:
PRIVACY_INPUT is a dictionary that contains all purpose items from the set of purposes PURPOSES
    Each element in PRIVACY_INPUT declares a purpose from PURPOSES, containing:
      - A list of data pairs (class_name, property_name) that describe personal data to be accessed (e.g., (Person, name)).
        (if no personal data is declared, leave the value as an empty list).
      - A dictionary of the children purpose.
        (if there are no child purposes, leave the value as an empty dictionary).
      - (Optional) An additional constraint description. This is for displaying in the privacy notice only, 
        as the actual implementation of the constraint must be implemented by you.
        If there is no additional constraint, you do not have to add it.

The following elements serve as an example. 
Your task is to define them according to the privacy requirements in the project description.
"""

PRIVACY_INPUT = {
    AnyPurpose: {
        "data": [("Person", "name"), ("Person", "manages")],
        "children": {
            MarketingPurpose: {
                "data": [],
                "children": {
                    MassMarketingPurpose: {
                        "data": [("Category", "name")],
                        "children": {},
                        "constraintDesc": "some other conditions"
                    }
                }
            }
        }
    },
    # This is only an example; your task is to define the elements according 
    # to the privacy requirements outlined in the project description.
    FunctionalPurpose: {
        "data": [],
        "children": {},
        "constraintDesc": "some conditions"
    }
    # ...
}


"""
Throw this exception when action is not authorized 
You can either use the default error page, or redirect to 
another page (+ its params), which will then have a 
notification at the bottom
"""
class SecurityException(Exception):
    def __init__(self, msg = 'Not allowed', page = 'sec_error.html', params = {}):
        self.msg = msg
        self.page = page
        self.params = params

"""
Throw this exception when action violates the privacy policy
You can either use the default error page or redirect to
another page (+ its params), which will then have a
notification at the bottom
"""
class PrivacyException(Exception):
    def __init__(self, msg = 'Not allowed', page = 'priv_error.html', params = {}):
        self.msg = msg
        self.page = page
        self.params = params

"""
Implement if you decide to use Flask-Principal
This function is called from app.py and it is 
needed for Flask-Principal. You can leave the function as 
is (i.e., unimplemented) if you opt not to use Flask-Principal.
"""
def on_identity_loaded(sender, identity):
    pass

"""
Use in case you need to initialize something
"""
def init():
    pass    

def main():
    user=PersonDTO.copy(current_user) 
    if current_user.is_authenticated:
        events = recommend_events(current_user)
    else:
        events = []
    return {'user' : user, 'recommended_events': events}

def profile():
    if not current_user.is_authenticated:
        raise SecurityException("You must be logged in to view your profile.")
    user=PersonDTO.copy(current_user) 

    restrict_user(user, user)

    for e in user.manages:
        e.owner = PersonDTO.copy(Event.query.get(e.id).owner)
        restrict_user(user, e.owner)
    for e in user.attends:
        e.owner = PersonDTO.copy(Event.query.get(e.id).owner)
        restrict_user(user, e.owner)
    subs=CategoryDTO.copies(current_user.subscriptions)
    for s in subs:
        for e in s.events:
            e.owner = PersonDTO.copy(Event.query.get(e.id).owner)
            restrict_user(user, e.owner)
        restrict_category(user, s)
    ad = get_personalize_ad(current_user)
    return {'user' : user, 'subs' : subs, 'ad': ad}
        
def events():   
    events = EventDTO.copies(Event.query.all())
    categories = CategoryDTO.copies(Category.query.all())

    user = PersonDTO.copy(current_user)
    for e in events:
        restrict_event(user, e)

    for c in categories:
        restrict_category(user, c)

    return {'events' : events, 'categories' : categories}

def view_event(id):
    user = PersonDTO.copy(current_user)
    restrict_user(user, user)
    event = EventDTO.copy(Event.query.get(id))
    restrict_event(user, event)
    return {'event' : event}

def edit_event(id):
    event = EventDTO.copy(Event.query.get(id))
    categories = CategoryDTO.copies(Category.query.all())

    user = PersonDTO.copy(current_user)
    restrict_user(user, user)

    for c in categories:
        restrict_category(user, c)

    # only managers can edit the event
    if not in_list(user, event.managedBy):
        raise SecurityException("You are not allowed to edit this event, because you are not manager of it.")
    return {'event' : event, 'categories' : categories}

@login_required
def update_event():
    event = Event.query.get(request.form["id"])
    user = PersonDTO.copy(current_user)

    if not in_list(user, event.managedBy):
        raise SecurityException("You are not allowed to edit this event, because you are not manager of it.")
    
    if event.title != request.form["title"]:
        event.title = request.form["title"]
    if event.description != request.form["description"]:
        event.description = request.form["description"]
    new_categories = request.form.getlist("categories")
    current_categories = [c.id for c in event.categories]
    if set(current_categories) != set(new_categories):
        categories = [Category.query.get(c) for c in new_categories]
        event.categories = categories
    db.session.commit()
    return request.form["id"]

@login_required
def join(id):
    event = Event.query.get(id)
    if current_user.id not in [p.id for p in event.requesters]:
        event.requesters.append(current_user)
        db.session.commit()

@login_required
def analyze(id):
    user = Person.query.get(current_user.id)
    if user.role.name != "ADMIN":
        raise SecurityException("You are not allowed to analyze this event, because you are not an admin.")
    
    event = Event.query.get(id)
    gender_counts = {"male": 0, "female": 0, "unknown": 0}
    for p in event.attendants:
        gender = p.gender if p.gender in gender_counts else "unknown"
        gender_counts[gender] += 1    
    return {
        'event': event,
        'male': gender_counts['male'],
        'female': gender_counts['female'],
        'unknown': gender_counts['unknown']
    }

@login_required   
def leave(id):
    event = Event.query.get(id)
    user = Person.query.get(current_user.id)

    if not user in event.attendants:
        raise SecurityException("You are not allowed to leave this event, because you are not attending it.")
    
    if user in event.managedBy:
        raise SecurityException("You are not allowed to leave this event, because you are managing it.")
                                
    for a in event.attendants:
        if a.id == current_user.id:
            event.attendants.remove(a)
            db.session.commit()
            break

@login_required
def create_event():
    # Check if the user is authenticated
    if not current_user.is_authenticated:
        raise SecurityException("You must be logged in to create an event.")
    
    title = request.form["title"]
    description = request.form["description"]
    owner = current_user
    categories = request.form.getlist("categories")
    categories = [Category.query.get(c) for c in categories]
    event = Event(title=title,
                  description=description,
                  owner=owner,
                  categories=categories)
    event.managedBy.append(owner)
    event.attendants.append(owner)
    db.session.add(event)
    db.session.commit()
    
@login_required
def manage_event(id):
    event = EventDTO.copy(Event.query.get(id))
    user = PersonDTO.copy(current_user)
    restrict_user(user, user)

    if not in_list(user, event.managedBy):
        raise SecurityException("You are not allowed to manage this event, because you are not manager of it.")
    return {'event' : event}

def categories():
    categories = CategoryDTO.copies(Category.query.all())

    user = PersonDTO.copy(current_user)
    restrict_user(user, user)
    for c in categories:
        restrict_category(user, c)
    return {'categories' : categories}

def view_category(id):
    category = CategoryDTO.copy(Category.query.get(id))
    user = PersonDTO.copy(current_user)
    restrict_user(user, user)
    restrict_category(user, category)

    return {'category' : category}

def remove_category(id,c):
    event = Event.query.get(id)
    category = Category.query.get(c)
    if event in category.events:
        category.events.remove(event)
        db.session.commit()
    
def edit_category(id):
    cat = Category.query.get(id)
    category = CategoryDTO.copy(cat)
    candidates = PersonDTO.copies(cat.candidates)
    return {'category' : category, 'candidates' : candidates}

def add_moderator(id,c):
    user = Person.query.get(id)
    category = Category.query.get(c)
    if user not in category.moderators:
        category.moderators.append(user)
        db.session.commit()

def remove_moderator(id,c):
    user = Person.query.get(id)
    category = Category.query.get(c)
    if user in category.moderators:
        category.moderators.remove(user)
        db.session.commit()

def update_category():
    category = Category.query.get(request.form["id"])
    if category.name != request.form["name"]:
        category.name = request.form["name"]
    db.session.commit()
    return request.form["id"]

def subscribe(id):
    category = Category.query.get(id)
    if category not in current_user.subscriptions:
         current_user.subscriptions.append(category)
         db.session.commit()
    
def unsubscribe(id):
    category = Category.query.get(id)
    if category in current_user.subscriptions:
         current_user.subscriptions.remove(category)
         db.session.commit()
    
def send_mass_advertisement(id):
    category = Category.query.get(id)
    for subscriber in category.subscribers:
        send_advertisement_to_user(subscriber)

@login_required
def create_category():
    # only admin can create a category
    if not current_user.role.name == "ADMIN":
        raise SecurityException("You are not allowed to create a category, because you are not an admin.")
    
    name = request.form["name"]
    category = Category(name=name)
    db.session.add(category)
    db.session.commit()

def users():
    users = PersonDTO.copies(Person.query.all())
    return {'users' : users}

def user(id):
    user = PersonDTO.copy(Person.query.get(id))
    cur_user = PersonDTO.copy(current_user)
    restrict_user(cur_user, cur_user)
    restrict_user(cur_user, user)

    roles = RoleDTO.copies(Role.query.all())
    return {'user' : user, 'roles' : roles}

def update_user():
    user = Person.query.get(request.form["id"])
    if user.name != request.form["name"]:
        user.name = request.form["name"]
    if user.surname != request.form["surname"]:
        user.surname = request.form["surname"]
    if user.role.name != request.form["role"]:
        user.role = Role.query.filter_by(name=request.form["role"]).first()
    if user.email != request.form["email"]:
        user.email = request.form["email"]
    if user.gender != request.form["gender"]:
        user.gender = request.form["gender"]
    db.session.commit()
    return request.form["id"]
        
def promote_manager(id,e):
    user = Person.query.get(id)
    event = Event.query.get(e)
    if user not in event.managedBy:
        event.managedBy.append(user)
        db.session.commit()  

def demote_manager(id,e):
    user = Person.query.get(id)
    event = Event.query.get(e)
    if user in event.managedBy:
        event.managedBy.remove(user)
        db.session.commit()

def remove_attendee(id,e):
    user = Person.query.get(id)
    event = Event.query.get(e)
    if user in event.attendants:
        event.attendants.remove(user)
        db.session.commit()

def accept_request(id,e):
    user = Person.query.get(id)
    event = Event.query.get(e)
    if user not in event.attendants:
        event.attendants.append(user)
    event.requesters.remove(user)
    db.session.commit()

def reject_request(id,e):
    user = Person.query.get(id)
    event = Event.query.get(e)
    event.requesters.remove(user)
    db.session.commit()

def ads():  
    ads = AdDTO.copies(Ad.query.all())
    return {'ads' : ads}    

def remove_ad(id):
    ad = Ad.query.get(id)
    db.session.delete(ad)
    db.session.commit()

def create_ad():
    content = request.form["content"]
    ad = Ad(content=content)
    db.session.add(ad)
    db.session.commit()

def recommend_events(user):
    subscriptions = user.subscriptions
    attending = user.attends
    events = [event for category in subscriptions for event in category.events]
    return list(set(events) - set(attending)) 
    
def get_personalize_ad(user):
    seed_string = f"{user.id}{user.name}{user.gender}"
    seed_value = int(hashlib.sha256(seed_string.encode()).hexdigest(), 16)
    random.seed(seed_value)
    ads = AdDTO.copies(Ad.query.all())
    if len(ads) == 0:
        return None
    else:
        return ads[random.randint(1, len(ads)) - 1]

def send_advertisement_to_user(user):
    if user.email:
        print(f'A generic advertisement was sent to {user.name} at email: {user.email}.', file=sys.stderr)


#### Helper functions ####
def in_list(target, list):
    if hasattr(target, 'id'):
        target_id = target.id
    else:
        target_id = -1

    if list == None:
        return False
    
    return any(obj.id == target_id for obj in list)


def restrict_event(user: PersonDTO, event: EventDTO, recursive: bool = True):
    full_event = EventDTO.copy(Event.query.get(event.id))
    managedBy = full_event.managedBy
    owner = full_event.owner
    
    if not in_list(user, managedBy) and not in_list(user, [owner]):
        event.requesters = []

    if not user.is_authenticated:
        event.attendants = []
        event.managedBy = []

def restrict_category(user: PersonDTO, category: CategoryDTO, recursive: bool = True):
    full_category = CategoryDTO.copy(Category.query.get(category.id))
    moderators = full_category.moderators

    if not in_list(user, moderators):
        category.subscribers = []
    else:
        category.subscribers = full_category.subscribers

    if recursive: # restrict access to all events under the category
        for event in category.events:
            restrict_event(user, event)

# restrict data concerning another user based on the requesters permissions and whether they are same person
def restrict_user(user: PersonDTO, user_to_restrict: PersonDTO, recursive: bool = True):
    if user_to_restrict == RESTRICTED:
        return
    
    if not user.is_authenticated:
        user_to_restrict.name=RESTRICTED
        user_to_restrict.surname=RESTRICTED
        user_to_restrict.username=RESTRICTED
        user_to_restrict.password=RESTRICTED
        user_to_restrict.email=RESTRICTED
        user_to_restrict.gender=RESTRICTED
        user_to_restrict.roles=RESTRICTED
        user_to_restrict.events=[]
        user_to_restrict.manages=[]
        user_to_restrict.attends=[]
        user_to_restrict.requests=[]
        user_to_restrict.subscriptions=[]
        return
    
    if not user.id == user_to_restrict.id:
        user_to_restrict.password=RESTRICTED
        user_to_restrict.username=RESTRICTED
        user_to_restrict.email=RESTRICTED
        user_to_restrict.gender=[]
        user_to_restrict.events=[]
        user_to_restrict.manages=[]
        user_to_restrict.attends=[]
        user_to_restrict.requests=[]
        user_to_restrict.subscriptions=[]
    elif recursive:
        for event in user_to_restrict.events:
            restrict_event(user, event)
        for event in user_to_restrict.manages:
            restrict_event(user, event)
        for event in user_to_restrict.attends:
            restrict_event(user, event)
        for event in user_to_restrict.requests:
            restrict_event(user, event)
        for category in user_to_restrict.subscriptions:
            restrict_category(user, category)
        for event in user_to_restrict.moderates:
            restrict_event(user, event)

