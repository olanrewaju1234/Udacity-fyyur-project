#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
from distutils.log import error
import sys
import json
from unicodedata import name
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from models import db, Artist, Venue, Show

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database



#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
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
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
    data = []
    results = Venue.query.distinct(Venue.city, Venue.state).all()
    for result in results:
        city_state_unit = {
            "city": result.city,
            "state": result.state
        }
        venues = Venue.query.filter_by(city=result.city, state=result.state).all()

        # format each venue
        formatted_venues = []
        for venue in venues:
            formatted_venues.append({
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": len(list(filter(lambda x: x.start_time > datetime.now(), venue.shows)))
            })
        
        city_state_unit["venues"] = formatted_venues
        data.append(city_state_unit)
   
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search_term = request.form.get('search_term')
    venues = Venue.query.filter(
      Venue.name.ilike('%{}%'.format(search_term))).all()

    data = []
    for venue in venues:
       value = {}
       value['id'] = venue.id
       value['name'] = venue.name
       value['num_upcoming_shows'] = len(venue.shows)
       data.append(value)

    response = {}
    response['count'] = len(data)
    response['data'] = data
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
    venue = Venue.query.get(venue_id)
    setattr(venue, "genres", venue.genres.split(",")) # convert genre string back to array
    
    #view past shows
    past_shows = list(filter(lambda show: show.start_time < datetime.now(), venue.shows))
    value_shows = []
    for show in past_shows:
        value = {}
        value["artist_name"] = show.artist.name
        value["artist_id"] = show.artist.id
        value["artist_image_link"] = show.artist.image_link
        value["start_time"] = show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
        value_shows.append(value)

    setattr(venue, "past_shows", value_shows)
    setattr(venue,"past_shows_count", len(past_shows))

    # view future shows
    upcoming_shows = list(filter(lambda show: show.start_time > datetime.now(), venue.shows))
    value_shows = []
    for show in upcoming_shows:
        value = {}
        value["artist_name"] = show.artist.name
        value["artist_id"] = show.artist.id
        value["artist_image_link"] = show.artist.image_link
        value["start_time"] = show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
        value_shows.append(value)

    setattr(venue, "upcoming_shows", value_shows)    
    setattr(venue,"upcoming_shows_count", len(upcoming_shows))

    return render_template('pages/show_venue.html', venue=venue)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  try:
    new_venue = Venue(
      name = request.form['name'],
      city = request.form['city'],
      state =request.form['state'],
      address = request.form['address'],
      phone = request.form['phone'],
      image_link = request.form['image_link'],
      facebook_link = request.form['facebook_link'],
      genres = ','.join(request.form.getlist('genres')),
      website = request.form['website_link'],
      seeking_talent = bool(request.form.getlist('seeking_talent')),
      description = request.form['seeking_description']
  )
    db.session.add(new_venue)
    db.session.commit()
    # on successful db insert, flash success
    flash('Venue' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Venue' + request.form['name'] + ' could not be listed.')
  finally:
    db.session.close()       
  return render_template('pages/home.html')
  

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
    flash("Venue " + venue.name + " was deleted successfully!")
  except:
    db.session.rollback()
    flash("Venue was not deleted successfully.")
  finally:
        db.session.close()
  return redirect(url_for('pages/home.html'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  return render_template('pages/artists.html', artists=Artist.query.all())

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
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

    for artist in artists:
        value = {}
        value["name"] = artist.name
        value["id"] = artist.id

        upcoming_shows = 0
        for show in artist.shows:
            if show.start_time > datetime.now():
                upcoming_shows = upcoming_shows + 1
        value["upcoming_shows"] = upcoming_shows

        response["data"].append(value)
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))
 
@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.get(artist_id)
    setattr(artist, "genres", artist.genres.split(",")) # convert genre string back to array
    # view past shows
    past_shows = list(filter(lambda show: show.start_time < datetime.now(), artist.shows))
    value_shows = []
    for show in past_shows:
        value = {}
        value["venue_name"] = show.venue.name
        value["venue_id"] = show.venue.id
        value["venue_image_link"] = show.venue.image_link
        value["start_time"] = show.start_time.strftime("%m/%d/%Y, %H:%M:%S")

        value_shows.append(value)

    setattr(artist, "past_shows", value_shows)
    setattr(artist, "past_shows_count", len(past_shows))


    # view upcoming shows
    upcoming_shows = list(filter(lambda show: show.start_time > datetime.now(), artist.shows))
    value_shows = []
    for show in upcoming_shows:
        value = {}
        value["venue_name"] = show.venue.name
        value["venue_id"] = show.venue.id
        value["venue_image_link"] = show.venue.image_link
        value["start_time"] = show.start_time.strftime("%m/%d/%Y, %H:%M:%S")

        value_shows.append(value)

    setattr(artist, "upcoming_shows", value_shows)
    setattr(artist, "upcoming_shows_count", len(upcoming_shows))

    return render_template('pages/show_artist.html', artist=artist)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  form.genres.data = artist.genres.split(",") # convert genre string back to array
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  try:
    artist = Artist.query.get(artist_id)
    artist.name = request.form['name'],
    artist.city = request.form['city'],
    artist.state =request.form['state'],
    artist.phone = request.form['phone'],
    artist.image_link = request.form['image_link'],
    artist.facebook_link = request.form['facebook_link'],
    artist.genres = ','.join(request.form.getlist('genres'))
    artist.website = request.form['website_link'],
    artist.seeking_venue = bool(request.form['seeking_venue'])
    artist.description = request.form['seeking_description']
    db.session.add(artist)
    db.session.commit()
    # on successful db insert, flash success
    flash('Artist' + request.form['name'] + ' was edited successfully')
  except:
    error = True
    db.session.rollback()
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Artist' + request.form['name']+ ' was not edited successful.')
  finally:
    db.session.close()       
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  form.genres.data = venue.genres.split(",") # convert genre string back to array
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  try:
    venue = Venue.query.get(venue_id)

    venue.name = request.form['name'],
    venue.city = request.form['city'],
    venue.state =request.form['state'],
    venue.address = request.form['address'],
    venue.phone = request.form['phone'],
    venue.image_link = request.form['image_link'],
    venue.facebook_link = request.form['facebook_link'],
    venue.genres = ','.join(request.form.getlist('genres')),
    venue.website = request.form['website_link'],
    venue.seeking_talent = bool(request.form['seeking_talent'])
    venue.description = request.form['seeking_description']
  
    db.session.add(venue)
    db.session.commit()
    # on successful db insert, flash success
    flash('Artist' + request.form['name'] + ' was edited successfully')
  except:
    db.session.rollback()
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Artist' + request.form['name']+ ' was not edited successful.')
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
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  
  try:
    new_Artist = Artist(
      name = request.form['name'],
      city = request.form['city'],
      state =request.form['state'],
      phone = request.form['phone'],
      image_link = request.form['image_link'],
      facebook_link = request.form['facebook_link'],
      genres = ','.join(request.form.getlist('genres')),
      website = request.form['website_link'],
      seeking_venue = bool(request.form.getlist('seeking_venue')),
      description = request.form['seeking_description']
  )
    db.session.add(new_Artist)
    db.session.commit()
    # on successful db insert, flash success
    flash('Artist' + request.form['name'] + ' was successfully listed!')
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Artist' + request.form['name'] + ' could not be listed.')
  finally:
    db.session.close()       
  return render_template('pages/home.html')
  # # on successful db insert, flash success
  # flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # # TODO: on unsuccessful db insert, flash an error instead.
  # # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  # return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
    data = []

    shows = Show.query.all()
    for show in shows:
        value = {}
        value["venue_id"] = show.venue.id
        value["venue_name"] = show.venue.name
        value["artist_id"] = show.artist.id
        value["artist_name"] = show.artist.name
        value["artist_image_link"] = show.artist.image_link
        value["start_time"] = show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
        
        data.append(value)
    
    return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()

  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
        formData = request.form
        new_show = Show(
           artist_id = formData['artist_id'],
           venue_id = formData['venue_id'],
           start_time = formData['start_time'],
        )
        try:
            db.session.add(new_show)
            db.session.commit()
            flash('Show was successfully listed!')
        except Exception:
            db.session.rollback()
            print(sys.exc_info())
            flash('An error occurred. Show could not be listed.')
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
