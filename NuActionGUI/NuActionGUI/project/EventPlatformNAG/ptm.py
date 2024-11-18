from model import Action, Constraint
from enum import auto, Enum
from privacy_model import PrivacyModel
import dtm

class EventPlatformNAGPrivacyModel(PrivacyModel):

    # Extensible model (default: nothing declared)

    class Purpose(Enum):
        
        TARGETEDMARKETING = auto()
        MASSMARKETING = auto()
        RECOMMENDEVENTS = auto()
        CORE = auto()
        ANALYTICS = auto()
        MARKETING = auto()
        FUNCTIONAL = auto()
        ANY = auto()
        
        

    personaldata = [
        {'resource': 'Person', 'subresource': 'name'},
        {'resource': 'Person', 'subresource': 'surname'},
        {'resource': 'Person', 'subresource': 'role'},
        {'resource': 'Person', 'subresource': 'gender'},
        {'resource': 'Person', 'subresource': 'email'},
        {'resource': 'Person', 'subresource': 'subscriptions'}
        ]
        
    model = [(Purpose.MARKETING, [{'resource': 'Person', 'subresource': 'name'}], Constraint.fullAccess, 'true'), (Purpose.CORE, [{'resource': 'Person', 'subresource': 'name'}, {'resource': 'Person', 'subresource': 'surname'}, {'resource': 'Person', 'subresource': 'role'}, {'resource': 'Person', 'subresource': 'subscriptions'}, {'resource': 'Person', 'subresource': 'gender'}, {'resource': 'Person', 'subresource': 'email'}], Constraint.fullAccess, 'true'), (Purpose.RECOMMENDEVENTS, [{'resource': 'Person', 'subresource': 'subscriptions'}], lambda self= None: self.role == dtm.Role.REGULARUSER, 'you_are_regular_user'), (Purpose.TARGETEDMARKETING, [{'resource': 'Person', 'subresource': 'gender'}], Constraint.fullAccess, 'true'), (Purpose.MASSMARKETING, [{'resource': 'Person', 'subresource': 'email'}], Constraint.fullAccess, 'true'), (Purpose.ANALYTICS, [{'resource': 'Person', 'subresource': 'gender'}], Constraint.fullAccess, 'true')]

EventPlatformNAGPrivacyModel.validate()