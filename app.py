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
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Show(db.Model):
  __tablename__ = 'Show'
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'),primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'),primary_key=True)
  start_time = db.Column(db.DateTime)

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    website = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(120))
    shows = db.relationship('Show',backref='venue',lazy=True)


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(120))
    shows = db.relationship('Show',backref='artist',lazy=True)
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(str(value))
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

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
  
  venues_grouped = db.session.query(Venue.city, Venue.state).distinct()
  data = []
  for venue in venues_grouped:
      venue = dict(zip(('city', 'state'), venue))
      venue['venues'] = []
      for venue_data in Venue.query.filter_by(city=venue['city'], state=venue['state']).all():
          shows = Show.query.filter_by(venue_id=venue_data.id).all()
          len_upcoming_shows = 0
          for show in shows:
            artist = Artist.query.filter_by(id=show.artist_id).first()
            if show.start_time >= datetime.now():
                len_upcoming_shows+=1
          venues_data = {
              'id': venue_data.id,
              'name': venue_data.name,
              'num_upcoming_shows': len_upcoming_shows
          }
          venue['venues'].append(venues_data)
      data.append(venue)

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  search = "%{}%".format(search_term)
  venues = Venue.query.filter(Venue.name.like(search)).all()
  response={
    "count": len(list(venues)),
    "data": venues
  }
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue= Venue.query.get(venue_id)
  shows = Show.query.filter_by(venue_id=venue_id)
  past_shows = []
  upcoming_shows = []
  for show in shows:
      artist = Artist.query.filter_by(id=show.artist_id).first()
      if show.start_time < datetime.now():
          past_shows.append({
              "artist_id": artist.id,
              "artist_name": artist.name,
              "artist_image_link": artist.image_link,
              "start_time": format_datetime(show.start_time)
          })
      else:
        upcoming_shows.append({
              "artist_id": artist.id,
              "artist_name": artist.name,
              "artist_image_link": artist.image_link,
              "start_time": format_datetime(show.start_time)
          })

  venue.past_shows_count = len(past_shows)
  venue.past_shows = past_shows
  venue.upcoming_shows_count = len(upcoming_shows)
  venue.upcoming_shows = upcoming_shows

  return render_template('pages/show_venue.html', venue=venue)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  venue = Venue()
  form = VenueForm()
  venue.name = form.name.data
  venue.city = form.city.data
  venue.state =  form.state.data
  venue.address =  form.address.data
  venue.state =  form.state.data
  venue.phone =  form.phone.data
  venue.image_link = form.image_link.data
  venue.website = form.website.data
  venue.genres = form.genres.data
  venue.facebook_link = form.facebook_link.data
  venue.seeking_description = form.seeking_description.data
  venue.seeking_talent = True if venue.seeking_description else False

  try:
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed. :c')
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully removed!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be removed. :c')
  finally:
    db.session.close()
 
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():

  search_term = request.form.get('search_term', '')
  search = "%{}%".format(search_term)
  artists = Artist.query.filter(Artist.name.like(search)).all()

  response={
    "count": len(list(artists)),
    "data": artists
  }

  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  
  artist= Artist.query.get(artist_id)
  shows = Show.query.filter_by(artist_id=artist_id)
  past_shows = []
  upcoming_shows = []
  for show in shows:
      venue = Venue.query.filter_by(id=show.venue_id).first()
      if show.start_time < datetime.now():
          past_shows.append({
              "venue_id": venue.id,
              "venue_name": venue.name,
              "venue_image_link": venue.image_link,
              "start_time": format_datetime(show.start_time)
          })
      else:
        upcoming_shows.append({
              "venue_id": venue.id,
              "venue_name": venue.name,
              "venue_image_link": venue.image_link,
              "start_time": format_datetime(show.start_time)
          })

  artist.past_shows_count = len(past_shows)
  artist.past_shows = past_shows
  artist.upcoming_shows_count = len(upcoming_shows)
  artist.upcoming_shows = upcoming_shows

  
  return render_template('pages/show_artist.html', artist=artist)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  form.name.data = artist.name 
  form.city.data = artist.city 
  form.facebook_link.data = artist.facebook_link
  form.genres.data = artist.genres 
  form.image_link.data = artist.image_link 
  form.phone.data = artist.phone 
  form.website.data = artist.website 
  form.seeking_description.data = artist.seeking_description  
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  artist.name = form.name.data
  artist.city = form.city.data
  artist.facebook_link = form.facebook_link.data
  artist.genres = form.genres.data
  artist.image_link = form.image_link.data
  artist.phone = form.phone.data
  artist.website = form.website.data
  artist.seeking_description = form.seeking_description.data
  artist.seeking_venue = True if artist.seeking_description else False
  try:
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully updated!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated. :c')
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)
  form = VenueForm()
  form.name.data=venue.name 
  form.city.data=venue.city 
  form.state.data=venue.state  
  form.address.data=venue.address 
  form.state.data=venue.state  
  form.phone.data=venue.phone 
  form.image_link.data=venue.image_link 
  form.website.data=venue.website 
  form.genres.data=venue.genres 
  form.facebook_link.data=venue.facebook_link  
  form.seeking_description.data=venue.seeking_description  
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  venue = Venue.query.get(venue_id)
  form = VenueForm()
  venue.name = form.name.data
  venue.city = form.city.data
  venue.state =  form.state.data
  venue.address =  form.address.data
  venue.state =  form.state.data
  venue.phone =  form.phone.data
  venue.image_link = form.image_link.data
  venue.website = form.website.data
  venue.genres = form.genres.data
  venue.facebook_link = form.facebook_link.data
  venue.seeking_description = form.seeking_description.data
  venue.seeking_talent = True if venue.seeking_description else False

  try:
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated. :c')
  finally:
    db.session.close()
    
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

  artist = Artist()
  artist.name = form.name.data
  artist.city = form.city.data
  artist.facebook_link = form.facebook_link.data
  artist.genres = form.genres.data
  artist.image_link = form.image_link.data
  artist.phone = form.phone.data
  artist.website = form.website.data
  artist.seeking_description = form.seeking_description.data
  artist.seeking_venue = True if artist.seeking_description else False
  try:
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed. :c')
  finally:
    db.session.close()
 
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  
  data = list(map(lambda x: 
  { 'venue_id': x.venue_id, 
    'venue_name': x.venue.name,
    'artist_id': x.artist.id,
    'artist_name': x.artist.name,
    'artist_image_link': x.artist.image_link,
    'start_time': x.start_time 
    },Show.query.all()))

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  show = Show()
  form = ShowForm()
  show.artist_id = form.artist_id.data
  show.venue_id = form.venue_id.data
  show.start_time = form.start_time.data

  try:
    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Show could not be listed. :c')
  finally:
    db.session.close()
  
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
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
