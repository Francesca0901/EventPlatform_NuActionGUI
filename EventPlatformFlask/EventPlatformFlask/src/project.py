from flask import request
from flask_user import current_user, login_required, roles_accepted
from model import Consent, db, Person, Role, Event, Category, Purpose, Ad, AnyPurpose, FunctionalPurpose, MarketingPurpose, AnalyticsPurpose, CorePurpose, RecommendEventsPurpose, TargetedMarketingPurpose, MassMarketingPurpose
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

# the name, surname, role, gender, and email attributes and the subscriptions association end in the Person entity
PRIVACY_INPUT = {
    AnyPurpose: {
        "data": [],
        "children": {
            MarketingPurpose: {
                "data": [("Person", "name")],
                "children": {
                    MassMarketingPurpose: {
                        "data": [("Person", "email")],
                        "children": {}
                    },
                    TargetedMarketingPurpose: {
                        "data": [("Person", "gender")],
                        "children": {}
                    }
                }
            },
            FunctionalPurpose: {
                "data": [],
                "children": {
                    CorePurpose: {
                        "data": [
                            ("Person", "name"), 
                            ("Person", "surname"), 
                            ("Person", "role"), 
                            ("Person", "subscriptions"), 
                            ("Person", "gender"), 
                            ("Person", "email")],
                        "children": {},
                    },
                    RecommendEventsPurpose: {
                        "data": [("Person", "subscriptions")],
                        "children": {},
                        "constraintDesc": "If you are a regular user"
                    }
                }
            },
            AnalyticsPurpose: {
                "data": [("Person", "gender")],
                "children": {}
            },
            
        }
    },
}

purpose_hierarchy = {
    TargetedMarketingPurpose: MarketingPurpose,
    MassMarketingPurpose: MarketingPurpose,
    RecommendEventsPurpose: FunctionalPurpose,
    CorePurpose: FunctionalPurpose,
    FunctionalPurpose: AnyPurpose,
    MarketingPurpose: AnyPurpose,
    AnalyticsPurpose: AnyPurpose,
}

def check_consent(user : PersonDTO, class_name, property_name, actual_purposes):
    # Ensure actual_purposes are Purpose objects
    if isinstance(actual_purposes[0], str):
        actual_purposes = [Purpose.query.filter_by(name=name).first() for name in actual_purposes]

    # check if the actual purpose is in the consented purposes
    for actual in actual_purposes:
        consent = Consent.query.filter_by(
            person_id = user.id,
            classname = class_name,
            propertyname = property_name,
            purpose_id = actual.id
        ).first()
        if not consent:
            # check parent purposes, in our case only one parent to check
            parent_purpose = purpose_hierarchy.get(actual.name)

            if parent_purpose:
                parent_purpose_id = Purpose.query.filter_by(name=parent_purpose).first().id
                consent = Consent.query.filter_by(
                    person_id=user.id,
                    classname=class_name,
                    propertyname=property_name,
                    purpose_id=parent_purpose_id
                ).first()
                if not consent:
                    # setattr(user, property_name, None)  # Set property to []
                    # raise PrivacyException(f"User {user.name} has not consented to the actual purpose {actual.name} or {parent_purpose} for {class_name}.{property_name}.")
                    return False
            else:
                # setattr(user, property_name, None)  # Set property to []
                # raise PrivacyException(f"User {user.name} has not consented to the actual purpose {actual.name} for {class_name}.{property_name}.")
                return False
            
    return True

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
    restrict_event(user, event)

    for c in categories:
        restrict_category(user, c)

    # only managers can edit the event
    if not in_list(event, user.manages):
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
    
    user = PersonDTO.copy(user)
    event = Event.query.get(id)
    gender_counts = {"male": 0, "female": 0, "unknown": 0}
    for p in event.attendants:
        p = PersonDTO.copy(p)
        restrict_user(user, p)

        # Privacy: if the user has not consented to gender
        if not check_consent(p, "Person", "gender", [AnalyticsPurpose]):
            p.gender = "unknown"
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
    restrict_event(user, event)

    # allow all user to view the manage_event endpoint, because user need to cancel there own request here.
    # if not in_list(user, event.managedBy):
    #     raise SecurityException("You are not allowed to manage this event, because you are not manager of it.")
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
    for e in category.events:
        e.owner = PersonDTO.copy(Event.query.get(e.id).owner)
    user = PersonDTO.copy(current_user)
    restrict_user(user, user)
    restrict_category(user, category)

    return {'category' : category}

@login_required
def remove_category(id,c):
    event = Event.query.get(id)
    category = Category.query.get(c)

    # manager can remove event's category
    # moderator can remove event from category they moderate
    
    user = PersonDTO.copy(current_user)
    if not in_list(user, event.managedBy) and not in_list(user, category.moderators):
        raise SecurityException("You are not allowed to remove this event from the category, because you are not manager or moderator.")
    
    if event in category.events:
        category.events.remove(event)
        db.session.commit()

@login_required
def edit_category(id):
    if not current_user.role.name == "ADMIN":
        raise SecurityException("You are not allowed to edit this category, because you are not an admin.")
    
    cat = Category.query.get(id)
    category = CategoryDTO.copy(cat)
    candidates = PersonDTO.copies(cat.candidates)
    return {'category' : category, 'candidates' : candidates}

@login_required
def add_moderator(id,c):
    if not current_user.role.name == "ADMIN":
        raise SecurityException("You are not allowed to add a moderator, because you are not an admin.")
    
    user = Person.query.get(id)
    category = Category.query.get(c)

    if user.role.name != "MODERATOR":
        raise SecurityException("You can only add a user with moderator role.")
    
    if user not in category.moderators:
        category.moderators.append(user)
        db.session.commit()

@login_required
def remove_moderator(id,c):
    # admin can remove user with moderator role from category they moderate
    # moderator can remove themselves from category they moderate
    user = Person.query.get(id)
    category = Category.query.get(c)

    if user.role.name != "MODERATOR":
        raise SecurityException("You can only remove a user with moderator role.")
    
    if not current_user.role.name == "ADMIN" and not current_user.id == id:
        raise SecurityException("You are not allowed to remove a moderator, because you are not an admin or the moderator herself.")
    
    if user in category.moderators:
        category.moderators.remove(user)
        db.session.commit()
    else:
        raise SecurityException("User is not a moderator of the category.")

@login_required
def update_category():
    if not current_user.role.name == "ADMIN":
        raise SecurityException("You are not allowed to update this category, because you are not an admin.")
    
    category = Category.query.get(request.form["id"])
    if category.name != request.form["name"]:
        category.name = request.form["name"]
    db.session.commit()
    return request.form["id"]

@login_required
def subscribe(id):
    category = Category.query.get(id)
    if category not in current_user.subscriptions:
         current_user.subscriptions.append(category)
         db.session.commit()
    
@login_required
def unsubscribe(id):
    category = Category.query.get(id)
    if category in current_user.subscriptions:
         current_user.subscriptions.remove(category)
         db.session.commit()
    else:
        raise SecurityException("You are not subscribed to this category.")

@login_required 
def send_mass_advertisement(id):
    # TODO: make sure
    # As only moderator can see the category subscribers' email, only they can ACTUALLY send mass advertisement
    category = Category.query.get(id)
    user = Person.query.get(current_user.id)

    category_dto = CategoryDTO.copy(category)
    user_dto = PersonDTO.copy(user)

    restrict_user(user_dto, user_dto)
    restrict_category(user_dto, category_dto)

    # can delete this, because if user is not a moderator, they can't see the subscribers
    if not in_list(user_dto, category_dto.moderators):
        raise SecurityException("You are not allowed to send mass advertisement, because you are not a moderator of the category.") 

    for subscriber in category_dto.subscribers:
        restrict_user(user_dto, subscriber)

        # Privacy: if the subscriber has not consented to the actual purpose TargetedMarketing, the email is restricted
        if not check_consent(subscriber, "Person", "email", [TargetedMarketingPurpose]):
            continue
    
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
    cur_user = PersonDTO.copy(current_user)
    restrict_user(cur_user, cur_user)
    for u in users:
        restrict_user(cur_user, u)
    return {'users' : users}

def user(id):
    user = PersonDTO.copy(Person.query.get(id))
    cur_user = PersonDTO.copy(current_user)
    restrict_user(cur_user, cur_user)
    restrict_user(cur_user, user)

    roles = RoleDTO.copies(Role.query.all())
    return {'user' : user, 'roles' : roles}

@login_required
def update_user():
    user = Person.query.get(request.form["id"])

    cur_user = PersonDTO.copy(current_user)

    # Admin can adit any user role, user can edit their own core info except role
    if not cur_user.role.name == "ADMIN" and not cur_user.id == user.id:
        raise SecurityException("You are not allowed to update this user, because you are not an admin or the user itself.")
    
    if user.name != request.form["name"]:
        if cur_user.id != user.id:
            raise SecurityException("You are not allowed to update this user's name.")
        user.name = request.form["name"]
    if user.surname != request.form["surname"]:
        if cur_user.id != user.id:
            raise SecurityException("You are not allowed to update this user's name.")
        user.surname = request.form["surname"]
    if user.role.name != request.form["role"]:
        if cur_user.role.name != "ADMIN":
            raise SecurityException("You are not allowed to update this user's role, because you are not an admin.")
        user.role = Role.query.filter_by(name=request.form["role"]).first()

    # Nobody can edit email and gender, so skip them
    # if user.email != request.form["email"]:
    #     user.email = request.form["email"]
    # if user.gender != request.form["gender"]:
    #     user.gender = request.form["gender"]
    db.session.commit()
    return request.form["id"]
        
@login_required
def promote_manager(id,e):
    user = Person.query.get(id)
    event = Event.query.get(e)

    if not in_list(current_user, event.managedBy):
        raise SecurityException("You are not allowed to promote a manager, because you are not manager of the event.")
    
    if not in_list(user, event.attendants):
        raise SecurityException("You are not allowed to promote a manager, because this user is not attending the event.")
    
    if user not in event.managedBy:
        event.managedBy.append(user)
        db.session.commit()  

@login_required
def demote_manager(id,e):
    user = Person.query.get(id)
    event = Event.query.get(e)

    # only owner can demote a manager, and owner can't demote themselves
    if not in_list(event, user.manages):
        raise SecurityException("You are not allowed to demote a manager, because you are not owner of the event.")
    
    if current_user.id == user.id:
        raise SecurityException("As an owner, you are not allowed to demote yourself.")
    
    if user in event.managedBy:
        event.managedBy.remove(user)
        db.session.commit()

@login_required
def remove_attendee(id,e):
    # any user except the managers can remove themselves
    # managers can remove any attendee if they are not managers

    cur_user = Person.query.get(current_user.id)
    user = Person.query.get(id)
    event = Event.query.get(e)

    if in_list(user, event.managedBy):
        raise SecurityException("You are not allowed to remove a manager as attendee.")
    
    if user.id == cur_user.id or in_list(cur_user, event.managedBy):
        if user in event.attendants:
            event.attendants.remove(user)
            db.session.commit()
    else:
        raise SecurityException("You are not allowed to remove another user as attendee, because you are not manager of the event.")

@login_required
def accept_request(id,e):
    user = Person.query.get(id)
    event = Event.query.get(e)

    cur_user = Person.query.get(current_user.id)
    if not in_list(cur_user, event.managedBy):
        raise SecurityException("You are not allowed to accept a request, because you are not manager of the event.")

    # Manager can add those who have requested to join an event as attendants
    if not in_list(user, event.requesters):
        raise SecurityException("User has not requested to join the event.")

    if user not in event.attendants:
        event.attendants.append(user)
    event.requesters.remove(user)
    db.session.commit()

@login_required
def reject_request(id,e):
    user = Person.query.get(id)
    event = Event.query.get(e)

    cur_user = Person.query.get(current_user.id)
    if not in_list(cur_user, event.managedBy):
        raise SecurityException("You are not allowed to reject a request, because you are not manager of the event.")
    
    if not in_list(user, event.requesters):
        raise SecurityException("User has not requested to join the event.")

    event.requesters.remove(user)
    db.session.commit()

def ads():  
    ads = AdDTO.copies(Ad.query.all())
    return {'ads' : ads}    

@login_required
def remove_ad(id):
    if not current_user.role.name == "ADMIN":
        raise SecurityException("You are not allowed to remove an ad, because you are not an admin.")
    ad = Ad.query.get(id)
    db.session.delete(ad)
    db.session.commit()

@login_required
def create_ad():
    # only admin can create an ad
    if not current_user.role.name == "ADMIN":
        raise SecurityException("You are not allowed to create an ad, because you are not an admin.")
    content = request.form["content"]
    ad = Ad(content=content)
    db.session.add(ad)
    db.session.commit()

def recommend_events(user):
    # TODO :: copy DTO cause events turn to 0
    # user = PersonDTO.copy(user, True)
    # restrict_user(user, user)

    subscriptions = user.subscriptions
    if not check_consent(user, "Person", "subscriptions", [RecommendEventsPurpose]):
        subscriptions = []
    attending = user.attends
    events = [event for category in subscriptions for event in category.events]
    return list(set(events) - set(attending)) 
    
def get_personalize_ad(user):
    user = PersonDTO.copy(user)
    actual_purpose = [TargetedMarketingPurpose]
    all_consent = check_consent(user, "Person", "gender", actual_purpose) and check_consent(user, "Person", "name", actual_purpose)

    if not all_consent:
        return None

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
    requesters = full_event.requesters
    
    if not in_list(user, managedBy) and not in_list(user, [owner]):
        event.requesters = []
        # can still see it's own request
        if in_list(user, requesters):
            event.requesters = [user]

    if not user.is_authenticated:
        event.attendants = []
        event.managedBy = []

    for a in event.attendants:
        restrict_user(user, a, False)
    for m in event.managedBy:
        restrict_user(user, m, False)
    for c in event.categories:
        restrict_category(user, c, False)

def restrict_category(user: PersonDTO, category: CategoryDTO, recursive: bool = True):
    full_category = CategoryDTO.copy(Category.query.get(category.id), True)
    moderators = full_category.moderators

    if not in_list(user, moderators):
        category.subscribers = []
    else:
        category.subscribers = full_category.subscribers

    if recursive: # restrict access to all events under the category
        for event in category.events:
            restrict_event(user, event, False)

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
        user_to_restrict.roles=[RESTRICTED] # otherwise the PersonDTO accessing role[0] will throw index error
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
        for e in user_to_restrict.events:
            restrict_event(user, e, False)
        for e in user_to_restrict.manages:
            restrict_event(user, e, False)
        for e in user_to_restrict.attends:
            restrict_event(user, e, False)
        for e in user_to_restrict.requests:
            restrict_event(user, e, False)
        for c in user_to_restrict.subscriptions:
            restrict_category(user, c, False)

    full_user_to_restrict = PersonDTO.copy(Person.query.get(user_to_restrict.id), True)
    # administrators can read any user’s name, surname, role, gender
    if user.role.name == "ADMIN":
        user_to_restrict.name = full_user_to_restrict.name
        user_to_restrict.surname = full_user_to_restrict.surname
        user_to_restrict.roles = full_user_to_restrict.roles
        user_to_restrict.gender = full_user_to_restrict.gender

    # moderators can read read the email of the subscribers of the category they moderate.
    elif user.role.name == "MODERATOR":
        for category in user_to_restrict.subscriptions:
            if in_list(user, category.moderators):
                user_to_restrict.email = full_user_to_restrict.email
                break