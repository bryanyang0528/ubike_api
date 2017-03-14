"""
Flask Documentation:     http://flask.pocoo.org/docs/
Jinja2 Documentation:    http://jinja.pocoo.org/2/documentation/
Werkzeug Documentation:  http://werkzeug.pocoo.org/documentation/

This file creates your application.
"""

import os
import requests
import urllib
import gzip
import json
import quadkey
from flask import Flask, jsonify, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy



app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'this_should_be_configured')
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/ubike'
db = SQLAlchemy(app)

###
# donwnload ubike data
###

def download_ubike():
    url = "https://tcgbusfs.blob.core.windows.net/blobyoubike/YouBikeTP.gz"
    urllib.urlretrieve(url, "data/ubike.gz")
    f = gzip.open('data/ubike.gz', 'r')
    jdata = f.read()
    f.close()
    data = json.loads(jdata)
    return data

###
# Create DB Model
###

# Station
class Station(db.Model):
    __tablename__ = "stations"
    sno = db.Column(db.String(10), primary_key=True)
    sna = db.Column(db.String(120), unique=True)
    lat = db.Column(db.Float(10))
    lng = db.Column(db.Float(10))
    quadkey = db.Column(db.String(17), index=True)
    mday = db.Column(db.BigInteger)

    def __init__(self, sno, sna, lat, lng, quadkey, mday):
        self.sno = sno
        self.sna = sna
        self.lat = lat
        self.lng = lng
        self.quadkey = quadkey
        self.mday = mday

    def __repr__(self):
        return 'No: %s, Name: %s' % (self.sno, self. sna)

###
# Routing for your application.
###

@app.route('/')
def home():
    """Render website's home page."""
    return render_template('home.html')


@app.route('/about/')
def about():
    """Render the website's about page."""
    return render_template('about.html')

###
# Update DB
###

@app.route('/update/', methods=['GET'])
def update():
    data = download_ubike()
    for k, v in data['retVal'].iteritems():
        if not db.session.query(Station).filter(Station.sno == v['sno']).count():
            reg = Station(v['sno'], v['sna'], v['lat'], v['lng'], 
                    str(quadkey.from_geo((v['lat'], v['lng']), 17)),  v['mday'])
            db.session.add(reg)
            db.session.commit()

    updated = data['retVal']['0134']['mday']
    return jsonify({'status': 'successed', 'updated': updated})

###
# The functions below should be applicable to all Flask apps.
###

@app.route('/<file_name>.txt')
def send_text_file(file_name):
    """Send your static text file."""
    file_dot_text = file_name + '.txt'
    return app.send_static_file(file_dot_text)


@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=600'
    return response


@app.errorhandler(404)
def page_not_found(error):
    """Custom 404 page."""
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(debug=True)
