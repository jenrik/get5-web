from get5 import app, db, flash_errors, config_setting
from models import User, Team

import countries
import logos
import steamid
import util
import os
import io

from werkzeug.utils import secure_filename
from PIL import Image 

from flask import Blueprint, request, render_template, flash, g, redirect, jsonify

from wtforms import (
    validators,
    StringField, BooleanField,
    SelectField, ValidationError)

from flask_wtf.file import FileField
from flask_wtf import FlaskForm
team_blueprint = Blueprint('team', __name__)


def valid_auth(form, field):
    # Ignore empty data fields
    if field.data is None or field.data == '':
        return

    # Otherwise validate and coerce to steam64
    suc, newauth = steamid.auth_to_steam64(field.data)
    if suc:
        field.data = newauth
    else:
        raise ValidationError('Invalid Steam ID')

def valid_file(form, field):
    mock = config_setting("TESTING")
    if mock:
        return
    filename = secure_filename(field.data.filename)
    # Safe method.
    if filename == '':
        return
    
    index_of_dot = filename.index('.')
    file_name_without_extension = filename[:index_of_dot]
    exists = os.path.isfile(app.config['LOGO_FOLDER'] + "/" + secure_filename(filename))
    if '.' not in filename:
        raise ValidationError('Image MUST be PNG.')
    elif filename.rsplit('.', 1)[1].lower() != 'png':
        raise ValidationError('Image MUST be PNG.')
    elif len(filename.rsplit('.', 1)[0]) > 3:
        raise ValidationError('Image name can only be 3 characters long.')
    elif exists:
        raise ValidationError('Image name already exists.')

    file = request.files['upload_logo']
    img = Image.open(file)
    width, height = img.size
    out = io.BytesIO()
    #img.save(out, format='png')
    if width != 64 or height != 64:
        app.logger.info("Resizing image as it is not 64x64.")
        img = img.resize((64,64),Image.ANTIALIAS)
        img.save(out, format='png')
        # check once more for size.
        if out.tell() > 10000:
            app.logger.info("Size: {}".format(out.tell()))
            raise ValidationError('Image is too large, must be 10kB or less.')
        img.save(os.path.join(app.config['LOGO_FOLDER'], filename),optimize=True)
    #elif out.tell() > 10000:
    #    raise ValidationError('Image is too large, must be 10kB or less.')
    else:
        img.save(os.path.join(app.config['LOGO_FOLDER'], filename),optimize=True)

class TeamForm(FlaskForm):
    mock = config_setting("TESTING")
    name = StringField('Team Name', validators=[
        validators.required(),
        validators.Length(min=-1, max=Team.name.type.length)])

    tag = StringField('Team Tag', validators=[
        validators.required(), validators.Length(min=-1, max=Team.tag.type.length)])

    flag_choices = [('', 'None')] + countries.country_choices
    country_flag = SelectField(
        'Country Flag', choices=flag_choices, default='')
    if mock:
        logo_choices=logos.get_logo_choices()
        logo = SelectField('Logo Name', choices=logo_choices, default='')
    else:
        logo = SelectField('Logo Name', default='')

    upload_logo = FileField(validators=[valid_file])
    # Possible to create loop and follow MAXPLAYERS from team model?
    auth1 = StringField('Player 1', validators=[valid_auth])
    auth2 = StringField('Player 2', validators=[valid_auth])
    auth3 = StringField('Player 3', validators=[valid_auth])
    auth4 = StringField('Player 4', validators=[valid_auth])
    auth5 = StringField('Player 5', validators=[valid_auth])
    auth6 = StringField('Player 6', validators=[valid_auth])
    auth7 = StringField('Player 7', validators=[valid_auth])
    public_team = BooleanField('Public Team')

    def get_auth_list(self):
        auths = []
        for i in range(1, 8):
            key = 'auth{}'.format(i)
            auths.append(self.data[key])

        return auths


@team_blueprint.route('/team/create', methods=['GET', 'POST'])
def team_create():
    mock = config_setting("TESTING")
    if not g.user:
        return redirect('/login')

    form = TeamForm()
    # We wish to query this every time, since we can now upload photos.
    if not mock:
        form.logo.choices=logos.get_logo_choices()
    if request.method == 'POST':
        num_teams = g.user.teams.count()
        max_teams = config_setting('USER_MAX_TEAMS')
        if max_teams >= 0 and num_teams >= max_teams and not g.user.admin:
            flash('You already have the maximum number of teams ({}) stored'.format(num_teams))

        elif form.validate():
            data = form.data
            auths = form.get_auth_list()
            name = data['name'].strip()
            tag = data['tag'].strip()
            flag = data['country_flag']
            logo = data['logo']

            # Update the logo. Passing validation we have the filename in the list now.
            if not mock and form.upload_logo.data.filename != '':
                filename = secure_filename(form.upload_logo.data.filename)
                index_of_dot = filename.index('.')
                newLogoDetail = filename[:index_of_dot]
                # Reinit our logos.
                logos.add_new_logo(newLogoDetail)
                data['logo'] = newLogoDetail

            team = Team.create(g.user, name, tag, flag, logo,
                               auths, data['public_team'] and g.user.admin)

            db.session.commit()
            app.logger.info(
                'User {} created team {}'.format(g.user.id, team.id))

            return redirect('/teams/{}'.format(team.user_id))

        else:
            flash_errors(form)

    return render_template('team_create.html', user=g.user, form=form,
                           edit=False, is_admin=g.user.admin)


@team_blueprint.route('/team/<int:teamid>', methods=['GET'])
def team(teamid):
    team = Team.query.get_or_404(teamid)
    return render_template('team.html', user=g.user, team=team)


@team_blueprint.route('/team/<int:teamid>/edit', methods=['GET', 'POST'])
def team_edit(teamid):
    mock = config_setting("TESTING")
    team = Team.query.get_or_404(teamid)
    if not team.can_edit(g.user):
        return 'Not your team', 400

    form = TeamForm()
    # We wish to query this every time, since we can now upload photos.
    if not mock:
        form.logo.choices=logos.get_logo_choices()
    if request.method == 'GET':
        # Set values here, as per new FlaskForms.
        form.name.data = team.name
        form.tag.data = team.tag
        form.country_flag.data = team.flag
        form.logo.data = team.logo
        form.auth1.data = team.auths[0]
        form.auth2.data = team.auths[1]
        form.auth3.data = team.auths[2]
        form.auth4.data = team.auths[3]
        form.auth5.data = team.auths[4]
        form.auth6.data = team.auths[5]
        form.auth7.data = team.auths[6]
        form.public_team.data = team.public_team
        return render_template('team_create.html', user=g.user, form=form,
                               edit=True, is_admin=g.user.admin)

    elif request.method == 'POST':
        if form.validate():
            data = form.data
            public_team = team.public_team
            if g.user.admin:
                public_team = data['public_team']

            # Update the logo. Passing validation we have the filename in the list now.
            if not mock and form.upload_logo.data.filename != '':
                filename = secure_filename(form.upload_logo.data.filename)
                index_of_dot = filename.index('.')
                newLogoDetail = filename[:index_of_dot]
                # Reinit our logos.
                logos.add_new_logo(newLogoDetail)
                data['logo'] = newLogoDetail


            team.set_data(data['name'], data['tag'], data['country_flag'],
                            data['logo'], form.get_auth_list(),
                            public_team)
            
            db.session.commit()
            return redirect('/teams/{}'.format(team.user_id))
        else:
            flash_errors(form)

    return render_template(
        'team_create.html', user=g.user, form=form, edit=True,
                           is_admin=g.user.admin)


@team_blueprint.route('/team/<int:teamid>/delete')
def team_delete(teamid):
    team = Team.query.get_or_404(teamid)
    if not team.can_delete(g.user):
        return 'Cannot delete this team', 400

    if Team.query.filter_by(id=teamid).delete():
        db.session.commit()

    return redirect('/myteams')


@team_blueprint.route('/teams/<int:userid>', methods=['GET'])
def teams_user(userid):
    user = User.query.get_or_404(userid)
    page = util.as_int(request.values.get('page'), on_fail=1)
    json_data = util.as_int(request.values.get('json'), on_fail=0)

    if json_data:
        teams_dict = {}
        for team in user.teams:
            team_dict = {}
            team_dict['name'] = team.name
            team_dict['tag'] = team.tag
            team_dict['flag'] = team.flag
            team_dict['logo'] = team.logo
            team_dict['players'] = filter(lambda x: bool(x), team.auths)
            teams_dict[team.id] = team_dict
        return jsonify(teams_dict)

    else:
        # Render teams page
        my_teams = (g.user is not None and userid == g.user.id)
        teams = user.teams.paginate(page, 20)
        return render_template(
            'teams.html', user=g.user, teams=teams, my_teams=my_teams,
                               page=page, owner=user)

@team_blueprint.route('/teams', methods=['GET'])
def all_teams():
    all_public_teams = Team.query.filter_by(public_team=True)
    page = util.as_int(request.values.get('page'), on_fail=1)
    json_data = util.as_int(request.values.get('json'), on_fail=0)

    if json_data:
        teams_dict = {}
        for team in all_public_teams:
            team_dict = {}
            team_dict['name'] = team.name
            team_dict['tag'] = team.tag
            team_dict['flag'] = team.flag
            team_dict['logo'] = team.logo
            team_dict['players'] = filter(lambda x: bool(x), team.auths)
            teams_dict[team.id] = team_dict
        return jsonify(teams_dict)

    else:
        # Render teams page
        teams = all_public_teams.paginate(page, 20)
        return render_template(
            'teams.html', user=g.user, teams=teams, my_teams=False,
                               page=page, owner=None)


@team_blueprint.route('/myteams', methods=['GET'])
def myteams():
    if not g.user:
        return redirect('/login')

    return redirect('/teams/' + str(g.user.id))
