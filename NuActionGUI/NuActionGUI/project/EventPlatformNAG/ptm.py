from model import Action, Constraint
from enum import auto, Enum
from privacy_model import PrivacyModel
import dtm

class EventPlatformNAGPrivacyModel(PrivacyModel):

    # Extensible model (default: nothing declared)

    class Purpose(Enum):
        
        pass
        

    personaldata = [
        ]
        
    model = []

EventPlatformNAGPrivacyModel.validate()