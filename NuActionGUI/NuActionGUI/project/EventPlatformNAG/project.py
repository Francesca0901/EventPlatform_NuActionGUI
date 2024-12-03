# Copyright (c) 2023 All Rights Reserved

from flask import render_template, redirect, url_for
from flask_user import current_user
from dtm import db, Event, Category, Person, Role, Ad, Invite
from auxiliary import recommend_events, get_personalize_ad, send_advertisement_to_user, get_candidates

def main(request):
    return render_template('main.html', user=current_user, recommended_events=recommend_events({'user': current_user}) if current_user.is_authenticated else [])

def users(request):
    return render_template('users.html', users=Person.query.all())

def user(request):
    return render_template('user.html', user=Person.query.get(request.args["id"]), roles=Role.getAuthenticatedRoles())

def profile(request):
    return render_template('profile.html', user=current_user, ad=get_personalize_ad({'user': current_user}))

def update_user(request):
    user = Person.query.get(request.form["id"])
    if user.name != request.form["name"]:
        user.name = request.form["name"]
    if user.surname != request.form["surname"]:
        user.surname = request.form["surname"]    
    if user.email != request.form["email"]:
        user.email = request.form["email"]
    if user.gender != request.form["gender"]:
        user.gender = request.form["gender"]
    if user.role.name != request.form["role"]:
        user.role = Role.query.filter_by(name=request.form["role"]).first()
    db.session.commit()
    return redirect(url_for('user',id=request.form["id"])) 


def join(request):
    event = Event.query.get(request.args["id"])
    if current_user.id not in [p.id for p in event.requesters]:
        p = Person.query.get(current_user.id)
        event.requesters.append(p)
        db.session.commit()
    return redirect(url_for('events'))


def leave(request):
    event = Event.query.get(request.args["id"])
    if current_user.id in [p.id for p in event.attendants]:
        p = Person.query.get(current_user.id)
        event.attendants.remove(p)
        db.session.commit()
    return redirect(url_for('profile'))


def add_moderator(request):
    user = Person.query.get(request.args["id"])
    category = Category.query.get(request.args["c"])
    if user not in category.moderators:
        category.moderators.append(user)
        db.session.commit()
    return redirect(url_for('edit_category',id=request.args["c"]))


def remove_moderator(request):
    user = Person.query.get(request.args["id"])
    category = Category.query.get(request.args["c"])
    if user in category.moderators:
        category.moderators.remove(user)
        db.session.commit()
    return redirect(url_for('edit_category',id=request.args["c"]))


def subscribe(request):
    category = Category.query.get(request.args["id"])
    if category not in current_user.subscriptions:
         current_user.subscriptions.append(category)
         db.session.commit()
    return redirect(url_for('categories'))


def unsubscribe(request):
    category = Category.query.get(request.args["id"])
    if category in current_user.subscriptions:
         current_user.subscriptions.remove(category)
         db.session.commit()
    return redirect(url_for('profile'))


def events(request):
    return render_template('events.html', events=Event.query.all(), categories=Category.query.all())


def create_event(request):
    event = Event()
    event.owner = current_user
    event.managedBy.append(current_user)
    event.attendants.append(current_user)
    event.title = request.form["title"]
    event.description = request.form["description"]
    categories = request.form.getlist("categories")
    for cid in categories:
        c = Category.query.get(cid)
        event.categories.append(c)
    db.session.add(event)
    db.session.commit()
    return redirect(url_for('events'))


def view_event(request):
    event=Event.query.get(request.args["id"])
    return render_template('view_event.html', event=Event.query.get(request.args["id"]), categories=Category.query.all())


def edit_event(request):
    return render_template('edit_event.html', event=Event.query.get(request.args["id"]), categories=Category.query.all())


def update_event(request):
    event = Event.query.get(request.form["id"])
    if event.title != request.form["title"]:
        event.title = request.form["title"]
    if event.description != request.form["description"]:
        event.description = request.form["description"]
    new_categories = [int(id) for id in request.form.getlist("categories")] 
    current_categories = [c.id for c in event.categories]
    if set(current_categories) != set(new_categories):
        ids_to_remove = set(current_categories) - set(new_categories)
        ids_to_add = set(new_categories) - set(current_categories)
        for cid in ids_to_remove:
            c = Category.query.get(cid)
            event.categories.remove(c)
        for cid in ids_to_add:
            c = Category.query.get(cid)
            event.categories.append(c)
    db.session.commit()
    return redirect(url_for('edit_event', id=request.form["id"]))


def manage_event(request):
    event = Event.query.get(request.args["id"])
    all_users = Person.query.all()
    invitees = list([i.invitee.id for i in event.invitations])
    attendants = list([a.id for a in event.attendants])
    requesters = list([r.id for r in event.requesters])
    users = []
    for u in all_users:
        if u.id not in invitees and u.id not in attendants and u.id not in requesters:
            users.append(u)
    return render_template('manage_event.html', 
        event=event,
        users=users)


def remove_category(request):
    event = Event.query.get(request.args["id"])
    category = Category.query.get(request.args["c"])
    if event in category.events:
        category.events.remove(event)
        db.session.commit()
    return redirect(url_for('view_category',id=request.args["c"]))


def promote_manager(request):
    user = Person.query.get(request.args["id"])
    event = Event.query.get(request.args["e"])
    if user not in event.managedBy:
        event.managedBy.append(user)
        db.session.commit()  
    return redirect(url_for('manage_event',id=request.args["e"]))


def demote_manager(request):
    user = Person.query.get(request.args["id"])
    event = Event.query.get(request.args["e"])
    if user in event.managedBy:
        event.managedBy.remove(user)
        db.session.commit()
    return redirect(url_for('manage_event',id=request.args["e"]))


def remove_attendee(request):
    user = Person.query.get(request.args["id"])
    event = Event.query.get(request.args["e"])
    if user in event.attendants:
        event.attendants.remove(user)
        db.session.commit()
    return redirect(url_for('manage_event',id=request.args["e"]))


def accept_request(request):
    user = Person.query.get(request.args["id"])
    event = Event.query.get(request.args["e"])
    if user not in event.attendants:
        event.attendants.append(user)
    event.requesters.remove(user)
    db.session.commit()
    return redirect(url_for('manage_event',id=request.args["e"]))


def reject_request(request):
    user = Person.query.get(request.args["id"])
    event = Event.query.get(request.args["e"])
    event.requesters.remove(user)
    db.session.commit()
    return redirect(url_for('manage_event',id=request.args["e"]))


def categories(request):
    return render_template('categories.html', categories=Category.query.all())


def create_category(request):    
    category = Category()
    category.name = request.form["name"]
    db.session.add(category)
    db.session.commit()
    return redirect(url_for('categories'))


def view_category(request):
    return render_template('view_category.html', category=Category.query.get(request.args["id"]))


def edit_category(request):
    category = Category.query.get(request.args["id"])
    candidates = get_candidates({'cat': category})
    return render_template('edit_category.html', category=category, candidates=candidates)


def update_category(request):
    category = Category.query.get(request.form["id"])
    if category.name != request.form["name"]:
        category.name = request.form["name"]
    db.session.commit()
    return redirect(url_for('edit_category',id=request.form["id"]))

def ads(request):  
    return render_template('ads.html', ads=Ad.query.all())

def remove_ad(request):
    ad = Ad.query.get(request.args["id"])
    ad.__delete__(db)
    db.session.commit()
    return redirect(url_for('ads'))

def create_ad(request):
    ad = Ad()
    ad.content = request.form["content"]
    db.session.add(ad)
    db.session.commit()
    return redirect(url_for('ads'))

def send_mass_advertisement(request):
    category = Category.query.get(request.args["id"])
    for p in category.subscribers:
        send_advertisement_to_user({'user': p})
    return redirect(url_for('categories'))

def analyze(request):
    event = Event.query.get(request.args["id"])
    gender_counts = {"male": 0, "female": 0, "unknown": 0}
    for p in event.attendants:
        gender = p.gender if p.gender in gender_counts else "unknown"
        gender_counts[gender] += 1    
    return render_template('analyze.html', event=event, male=gender_counts['male'], female=gender_counts['female'], unknown=gender_counts['unknown'])

def personalized_stats(request):
    return render_template('personalized_stats.html', user=current_user)

def send_invite(request):
    user = Person.query.get(request.args["id"])
    event = Event.query.get(request.args["e"])
    invite = Invite()
    invite.event = event
    invite.invitedBy = current_user
    invite.invitee = user
    db.session.commit()
    return redirect(url_for('manage_event', id=request.args["e"]))


def accept_invitation(request):
    invite = Invite.query.get(request.args["id"])
    event = invite.event
    user = invite.invitee
    event.attendants.append(user)
    invite.__delete__(db)
    db.session.commit()
    return redirect(url_for('profile'))


def decline_invitation(request):
    invite = Invite.query.get(request.args["id"])
    invite.__delete__(db)
    db.session.commit()
    return redirect(url_for('profile'))

