#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys
from sqlalchemy.orm import sessionmaker
import sqlalchemy as db
engine = db.create_engine('postgresql://postgres:@localhost:5432/fyyur')
Session = sessionmaker(bind=engine)
session = Session()
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(500))
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=False)
    shows = db.relationship("Show", backref="venues",
                            lazy=False, cascade="all, delete-orphan")


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(500))
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=False)
    shows = db.relationship("Show", backref="artists",
                            lazy=False, cascade="all, delete-orphan")


# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
    __tablename__ = "shows"

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey(
        "Artist.id"), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey(
        "venues.id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)

    def __repr__(self):
        return f"<Show id={self.id} artist_id={self.artist_id} venue_id={self.venue_id} start_time={self.start_time}"

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')

#  Venues
#  ----------------------------------------------------------------


@app.route('/venues')
def venues():
    all_venues = Venue.query.all()
    distinct_venues = Venue.query.distinct(Venue.city, Venue.state).all()
    venue_data = [
        {
            "city": venue.city,
            "state": venue.state,
            "venues": [
                {
                    'id': ven.id, "name": ven.name,
                    "num_upcoming_shows": len(list(filter(lambda x: x.start_time > datetime.now(), ven.shows)))
                } for ven in all_venues if ven.city == venue.city and ven.state == venue.state],

        } for venue in distinct_venues]
    return render_template('pages/venues.html', areas=venue_data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term', '')
    query = Venue.query.filter(Venue.name.ilike('%' + search_term + '%'))
    venue_list = [{
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": len(venue.shows),
    } for venue in query]
    response = {
        "count": len(venue_list),
        "data": venue_list
    }

    return render_template('pages/search_venues.html', results=response, search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)
    setattr(venue, "genres", venue.genres.split(","))

    past_shows = list(filter(lambda show: show.start_time <
                      datetime.now(), venue.shows))
    temp_shows = [
        {
            "artist_name": item.artists.name,
            "artist_id": item.artists.id,
            "artist_image_link": item.artists.image_link,
            "start_time": item.start_time.strftime("%m/%d/%Y, %H:%M:%S")
        } for item in past_shows]

    setattr(venue, "past_shows", temp_shows)
    setattr(venue, "past_shows_count", len(past_shows))

    upcoming_shows = list(
        filter(lambda show: show.start_time > datetime.now(), venue.shows))
    temp_shows = []
    temp_shows = [
        {
            "artist_name": item.artists.name,
            "artist_id": item.artists.id,
            "artist_image_link": item.artists.image_link,
            "start_time": item.start_time.strftime("%m/%d/%Y, %H:%M:%S")
        } for item in upcoming_shows]

    setattr(venue, "upcoming_shows", temp_shows)
    setattr(venue, "upcoming_shows_count", len(upcoming_shows))
    return render_template('pages/show_venue.html', venue=venue)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm(request.form)

    if form.validate():
        try:
            new_venue = Venue(
                name=form["name"].data,
                city=form["city"].data,
                state=form["state"].data,
                address=form["address"].data,
                phone=form["phone"].data,
                image_link=form["image_link"].data,
                genres=request.form.getlist('genres'),
                facebook_link=form["facebook_link"].data,
                website=form["website_link"].data,
                seeking_talent=form["seeking_talent"].data,
                seeking_description=form["seeking_description"].data
            )
            db.session.add(new_venue)
            db.session.commit()
            flash(
                'Venue ' + request.form['name'] + ' was successfully listed!')

        except Exception:
            db.session.rollback()
            print(sys.exc_info())
            flash('An error occurred. Venue ' +
                  request.form['name'] + ' could not be listed.')

        finally:
            db.session.close()
    else:
        flash('An error occurred while trying to create venue. Venue ' +
              request.form['name'] + ' could not be created.')

    return redirect(url_for("index"))


@app.route('/venues/<venue_id>/delete', methods=['GET'])
def delete_venue(venue_id):
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
        flash("Venue " + venue.name + " was deleted successfully!")
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash("Venue was not deleted successfully.")
    finally:
        db.session.close()

    return redirect(url_for("index"))


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    artists = Artist.query.all()

    data = []
    for item in artists:
        artist = {}
        artist["name"] = item.name
        artist["id"] = item.id

        upcoming_shows = 0
        for show in item.shows:
            if show.start_time > datetime.now():
                upcoming_shows += 1
        artist["upcoming_shows"] = upcoming_shows

        data.append(artist)
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term', '')
    artists = Artist.query.filter(
        Artist.name.ilike(f"%{search_term}%") |
        Artist.city.ilike(f"%{search_term}%") |
        Artist.state.ilike(f"%{search_term}%")
    ).all()
    response = {
        "count": len(artists),
        "data": []
    }

    for item in artists:
        artist = {}
        artist["name"] = item.name
        artist["id"] = item.id

        upcoming_shows = 0
        for show in item.shows:
            if show.start_time > datetime.now():
                upcoming_shows += 1
        artist["upcoming_shows"] = upcoming_shows

        response["data"].append(artist)

    return render_template('pages/search_artists.html', results=response, search_term=search_term)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.get(artist_id)
    setattr(artist, "genres", artist.genres.split(","))

    past_shows = list(filter(lambda show: show.start_time <
                      datetime.now(), artist.shows))
    temp_shows = [{
        "venue_id":  show.venues.name,
        "venue_name": show.venues.id,
        "venue_image_link": show.venues.image_link,
        "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
    } for show in past_shows]
    setattr(artist, "past_shows", temp_shows)
    setattr(artist, "past_shows_count", len(past_shows))

    upcoming_shows = list(
        filter(lambda show: show.start_time > datetime.now(), artist.shows))
    temp_shows = [{
        "venue_id":  show.venues.name,
        "venue_name": show.venues.id,
        "venue_image_link": show.venues.image_link,
        "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
    } for show in upcoming_shows]
    setattr(artist, "upcoming_shows", temp_shows)
    setattr(artist, "upcoming_shows_count", len(upcoming_shows))

    return render_template('pages/show_artist.html', artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    form.genres.data = artist.genres.split(",")

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    form = ArtistForm(request.form)

    if form.validate():
        try:
            artist = Artist.query.get(artist_id)
            artist.name = form["name"].data
            artist.city = form["city"].data
            artist.state = form["state"].data
            artist.phone = form["phone"].data
            artist.genres = request.form.getlist('genres')
            artist.facebook_link = form["facebook_link"].data
            artist.image_link = form["image_link"].data
            artist.seeking_venue = form["seeking_venue"].data
            artist.seeking_description = form["seeking_description"].data
            artist.website = form["website_link"].data
            db.session.add(artist)
            db.session.commit()
            flash("Artist " + artist.name + " was successfully edited!")
        except:
            db.session.rollback()
            print(sys.exc_info())
            flash("Artist " + form["name"] + "was not edited successfully.")
        finally:
            db.session.close()
    else:
        flash("Invalid form. Please fill in the appropriate data")

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    form.genres.data = venue.genres.split(",")
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form = VenueForm(request.form)

    if form.validate():
        try:
            venue = Venue.query.get(venue_id)
            venue.name = form.name.data
            venue.city = form.city.data
            venue.state = form.state.data
            venue.address = form.address.data
            venue.phone = form.phone.data
            venue.genres = request.form.getlist('genres')
            venue.facebook_link = form.facebook_link.data
            venue.image_link = form.image_link.data
            venue.seeking_talent = form.seeking_talent.data
            venue.seeking_description = form.seeking_description.data
            venue.website = form.website_link.data

            db.session.add(venue)
            db.session.commit()

            flash("Venue " + form.name.data + " edited successfully.")

        except Exception:
            db.session.rollback()
            print(sys.exc_info())
            flash("Unable to edit venue.")
        finally:
            db.session.close()
    else:
        flash("Unable to edit venue.")

    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form = ArtistForm(request.form)

    if form.validate():
        try:
            new_artist = Artist(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                phone=form.phone.data,
                genres=request.form.getlist('genres'),
                image_link=form.image_link.data,
                facebook_link=form.facebook_link.data,
                website=form.website_link.data,
                seeking_venue=form.seeking_venue.data,
                seeking_description=form.seeking_description.data,
            )
            db.session.add(new_artist)
            db.session.commit()
            flash("Artist " + request.form["name"] +
                  " was successfully listed!")
        except Exception:
            db.session.rollback()
            flash("Artist was not successfully listed.")
        finally:
            db.session.close()
    else:
        print(form.errors)
        flash("Artist was not successfully listed.")

    return redirect(url_for("index"))


#  Shows
#  ----------------------------------------------------------------
@app.route('/shows')
def shows():
    shows = Show.query.all()
    data = [{
        "venue_id": show.venues.id,
        "venue_name": show.venues.name,
        "artist_id": show.artists.id,
        "artist_name": show.artists.name,
        "artist_image_link": show.artists.image_link,
        "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
    } for show in shows]
  
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form = ShowForm(request.form)
    if form.validate():
        try:
            new_show = Show(
                artist_id=form.artist_id.data,
                venue_id=form.venue_id.data,
                start_time=form.start_time.data
            )
            db.session.add(new_show)
            db.session.commit()
            flash('Show was successfully listed!')
        except Exception:
            db.session.rollback()
            print(sys.exc_info())
            flash('Show was not successfully listed.')
        finally:
            db.session.close()
    else:
        print(form.errors)
        flash('Show was not successfully listed.')

    return redirect(url_for("index"))


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
