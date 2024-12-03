# Copyright (c) 2023 All Rights Reserved
# Generated code

from application import app
from flask import render_template, redirect, url_for, request, jsonify
from flask_user import UserManager, user_registered, login_required, current_user
from dtm import db, Person, VISITOR, REGULARUSER, MODERATOR, ADMIN,  Role, Purpose, Consent, PersonalData
from instrumentation import SecurityException, secure
from ptm import EventPlatformNAGPrivacyModel
import logging

@user_registered.connect_via(app)
def after_user_registered_hook(sender, user, **extra):
    role = Role.query.filter_by(name=REGULARUSER).one()
    user.role=role
    db.session.commit()

db.init_app(app)

# Silence passlib warning due to Flask-User not using the latest passlib version
logging.getLogger('passlib').setLevel(logging.ERROR)

with app.app_context():
    db.create_all()

    roles = Role.query.all()
    if len(roles) == 0:
        db.session.add(Role(name=VISITOR))
        db.session.add(Role(name=REGULARUSER))
        db.session.add(Role(name=MODERATOR))
        db.session.add(Role(name=ADMIN))
        db.session.commit()

    purposes = Purpose.query.all()
    if len(purposes) == 0:
        db.session.commit()
        
    personaldata = PersonalData.query.all()
    if len(personaldata) == 0:
        db.session.commit()

    def P(ls):
        def lazy():
            return list(map(lambda x: Purpose.query.filter_by(name=x).first(),ls))
        return lazy

user_manager = UserManager(app, db,Person)

# ENDPOINTS

def build_purpose_hierarchy(model):
    purpose_hierarchy = {}
    all_purposes = set()
    sub_purposes = set()
    for p, rs, _, d in model:
        purpose = Purpose.query.filter_by(name=p.name).first()
        all_purposes.add(purpose.name)
        if purpose.name not in purpose_hierarchy:
            purpose_hierarchy[purpose.name] = []
        subpurposes = purpose.subpurposes if hasattr(purpose, 'subpurposes') else []
        for subpurpose in subpurposes:
            if subpurpose.name not in purpose_hierarchy[purpose.name]:
                purpose_hierarchy[purpose.name].append(subpurpose)
            if subpurpose.name not in purpose_hierarchy:
                purpose_hierarchy[subpurpose.name] = []
            sub_purposes.add(subpurpose.name)
    top_level_purposes = list(all_purposes - sub_purposes)
    return purpose_hierarchy, top_level_purposes

def find_personal_data(resource, subresource):
    pds = list(PersonalData.query.all())
    for pd in pds:
        if pd.resource == resource and pd.subresource == subresource:
            return pd
    return None

@app.get('/policy')
@login_required
@secure(db,P([]))
def policy():
    consents = Consent.query.filter_by(user_id=current_user.id).all()
    model = EventPlatformNAGPrivacyModel.model
    hierarchymodel, toplevel = build_purpose_hierarchy(model)
    newmodel = {}
    tmpmodel = {}
    # purpose, resource, conditional, description
    for p,rs,_,d in model:
        purpose = Purpose.query.filter_by(name=p.name).first()

        for r in rs:
            data = find_personal_data(r['resource'],r['subresource'])
            c = list(filter((lambda x: purpose in x.purposes and x.data == data),consents))
            a = r.get("subresource",r.get("ends", None))
            r = r["resource"]
            c = c[0] if len(c) > 0 else None
            if  tmpmodel.get((purpose,r,d,c),None) != None and a != None:
                tmpmodel[(purpose,r,d,c)].append(a)
            else:
                tmpmodel[(purpose,r,d,c)] = [a] if a != None else []

    
    for k in tmpmodel.keys():
        (p,r,d,c) = k
        a = tmpmodel[k]
        if p not in newmodel:
            newmodel[p] = [(a,r,d,c)]
        else:
            newmodel[p].append((a,r,d,c))
    return render_template('privacy.html', model=newmodel, hierarchymodel=hierarchymodel, toplevel=toplevel)

@app.route('/add_consent/<int:purposeid>', methods=['POST'])
@login_required
# @secure(db,P([]))
def add_consent(purposeid):
    data = request.get_json()
    pd = find_personal_data(data.get('personalData'), data.get('classData'))
    p = Purpose.query.filter_by(id=purposeid).first()
    c = Consent.query.filter_by(user_id=current_user.id,data=pd).first()
    
    if c is not None and p in c.purposes:
        return redirect(url_for('policy'))
    c = Consent(data=pd, user=current_user)
    c.purposes.append(p)
    db.session.add(c)
    db.session.commit()
    return redirect(url_for('policy'))

@app.route('/remove_consent/<int:purposeid>', methods=['DELETE'])
@login_required
# @secure(db,P([]))
def remove_consent(purposeid):
    data = request.get_json()
    pd = find_personal_data(data.get('personalData'), data.get('classData'))
    p = Purpose.query.filter_by(id=purposeid).first()
    cs = Consent.query.filter_by(user_id=current_user.id,data=pd).all()

    for c in cs:
        if p in c.purposes:
            db.session.delete(c)
    db.session.commit()

    return jsonify({ 'success': True })

@app.route('/error')
def error():
    msg = "You are not allowed to access this page: Not a User"
    return render_template('error.html', message = msg)

@app.route('/')
@secure(db,P([]))
def main():
    from project import main 
    return main(request)

@app.route('/users', methods=['POST', 'GET'])
@secure(db,P([]))
def users():
    from project import users 
    return users(request)


@app.route('/user', methods=['POST', 'GET'])
@secure(db,P([]))
def user():
    from project import user 
    return user(request)


@app.route('/profile', methods=['POST', 'GET'])
@secure(db,P([]))
def profile():
    from project import profile 
    return profile(request)


@app.route('/update_user', methods=['POST', 'GET'])
@secure(db,P([]))
def update_user():
    from project import update_user 
    return update_user(request)


@app.route('/join', methods=['POST', 'GET'])
@secure(db,P([]))
def join():
    from project import join 
    return join(request)


@app.route('/leave', methods=['POST', 'GET'])
@secure(db,P([]))
def leave():
    from project import leave 
    return leave(request)


@app.route('/add_moderator', methods=['POST', 'GET'])
@secure(db,P([]))
def add_moderator():
    from project import add_moderator 
    return add_moderator(request)


@app.route('/remove_moderator', methods=['POST', 'GET'])
@secure(db,P([]))
def remove_moderator():
    from project import remove_moderator 
    return remove_moderator(request)


@app.route('/subscribe', methods=['POST', 'GET'])
@secure(db,P([]))
def subscribe():
    from project import subscribe 
    return subscribe(request)


@app.route('/unsubscribe', methods=['POST', 'GET'])
@secure(db,P([]))
def unsubscribe():
    from project import unsubscribe 
    return unsubscribe(request)




@app.route('/personalized_stats', methods=['POST', 'GET'])
@secure(db,P([]))
def personalized_stats():
    from project import personalized_stats 
    return personalized_stats(request)


@app.route('/events', methods=['POST', 'GET'])
@secure(db,P([]))
def events():
    from project import events 
    return events(request)


@app.route('/create_event', methods=['POST', 'GET'])
@secure(db,P([]))
def create_event():
    from project import create_event 
    return create_event(request)


@app.route('/view_event', methods=['POST', 'GET'])
@secure(db,P([]))
def view_event():
    from project import view_event 
    return view_event(request)


@app.route('/edit_event', methods=['POST', 'GET'])
@secure(db,P([]))
def edit_event():
    from project import edit_event 
    return edit_event(request)


@app.route('/update_event', methods=['POST', 'GET'])
@secure(db,P([]))
def update_event():
    from project import update_event 
    return update_event(request)


@app.route('/manage_event', methods=['POST', 'GET'])
@secure(db,P([]))
def manage_event():
    from project import manage_event 
    return manage_event(request)


@app.route('/remove_category', methods=['POST', 'GET'])
@secure(db,P([]))
def remove_category():
    from project import remove_category 
    return remove_category(request)


@app.route('/promote_manager', methods=['POST', 'GET'])
@secure(db,P([]))
def promote_manager():
    from project import promote_manager 
    return promote_manager(request)


@app.route('/demote_manager', methods=['POST', 'GET'])
@secure(db,P([]))
def demote_manager():
    from project import demote_manager 
    return demote_manager(request)


@app.route('/remove_attendee', methods=['POST', 'GET'])
@secure(db,P([]))
def remove_attendee():
    from project import remove_attendee 
    return remove_attendee(request)


@app.route('/accept_request', methods=['POST', 'GET'])
@secure(db,P([]))
def accept_request():
    from project import accept_request 
    return accept_request(request)


@app.route('/reject_request', methods=['POST', 'GET'])
@secure(db,P([]))
def reject_request():
    from project import reject_request 
    return reject_request(request)


@app.route('/analyze', methods=['POST', 'GET'])
@secure(db,P([]))
def analyze():
    from project import analyze 
    return analyze(request)


@app.route('/categories', methods=['POST', 'GET'])
@secure(db,P([]))
def categories():
    from project import categories 
    return categories(request)


@app.route('/create_category', methods=['POST', 'GET'])
@secure(db,P([]))
def create_category():
    from project import create_category 
    return create_category(request)


@app.route('/view_category', methods=['POST', 'GET'])
@secure(db,P([]))
def view_category():
    from project import view_category 
    return view_category(request)


@app.route('/edit_category', methods=['POST', 'GET'])
@secure(db,P([]))
def edit_category():
    from project import edit_category 
    return edit_category(request)


@app.route('/update_category', methods=['POST', 'GET'])
@secure(db,P([]))
def update_category():
    from project import update_category 
    return update_category(request)


@app.route('/send_mass_advertisement', methods=['POST', 'GET'])
@secure(db,P([]))
def send_mass_advertisement():
    from project import send_mass_advertisement 
    return send_mass_advertisement(request)



@app.route('/ads', methods=['POST', 'GET'])
@secure(db,P([]))
def ads():
    from project import ads 
    return ads(request)


@app.route('/create_ad', methods=['POST', 'GET'])
@secure(db,P([]))
def create_ad():
    from project import create_ad 
    return create_ad(request)


@app.route('/remove_ad', methods=['POST', 'GET'])
@secure(db,P([]))
def remove_ad():
    from project import remove_ad 
    return remove_ad(request)



@app.route('/send_invite', methods=['POST', 'GET'])
@secure(db,P([]))
def send_invite():
    from project import send_invite 
    return send_invite(request)


@app.route('/accept_invitation', methods=['POST', 'GET'])
@secure(db,P([]))
def accept_invitation():
    from project import accept_invitation 
    return accept_invitation(request)


@app.route('/decline_invitation', methods=['POST', 'GET'])
@secure(db,P([]))
def decline_invitation():
    from project import decline_invitation 
    return decline_invitation(request)

