"""
Flask Documentation:     http://flask.pocoo.org/docs/
Jinja2 Documentation:    http://jinja.pocoo.org/2/documentation/
Werkzeug Documentation:  http://werkzeug.pocoo.org/documentation/

This file creates your application.
"""

import os
import requests
import urllib, urllib3
import gzip
import json
import quadkey
from math import radians, cos, sin, asin, sqrt
from flask import Flask, jsonify, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy



app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'this_should_be_configured')
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/ubike'
app.config['SQLALCHEMY_NATIVE_UNICODE'] = 'utf-8'
app.config['JSON_AS_ASCII'] = False
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
# Find stations in the same quadkey
###
def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r

def find_stations(lat, lng):
    dist = {}
    result = []
    user_quadkey = str(quadkey.from_geo((lat, lng), 14))
    stations = Station.query.filter(Station.quadkey.like('%s%%' % user_quadkey)).all()
    print user_quadkey, stations
    if len(stations) > 0:
    
        sno_candidate = [x.sno for x in stations]
        sbis = Sbi.query.filter(Sbi.sno.in_(sno_candidate)).all()
        print sbis
        for i in xrange(len(sbis)):   
            sbi = sbis[i] 
            if sbi.sbi > 0 and sbi.act > 0 :
                detail = {}
                detail['dist'] = haversine(float(lat), float(lng), stations[i].lat, stations[i].lng)
                detail['sna'] = stations[i].sna
                detail['sbi'] = sbi.sbi
                detail['act'] = sbi.act
                print sbi.sno
                dist[sbi.sno] = detail
    
    
    print dist
    if len(dist) >= 2:
        tmp = sorted([i[1]['dist'] for i in dist.items()])[:2]
        for k, v in dist.iteritems():
            if v['dist'] in tmp:
                result.append({'station':v['sna'], 'num_bike':v['sbi']})
    else:
        result = []
    return result


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
        return '<Station %s>' % self.sno

class Sbi(db.Model):
    __tablename__ = "sbi"
    sno = db.Column(db.String(10), primary_key=True)
    sbi = db.Column(db.Integer)
    act = db.Column(db.Integer)
    mday = db.Column(db.BigInteger)

    def __init__(self, sno, sbi, act, mday):
        self.sno = sno
        self.sbi = sbi
        self.act = act
        self.mday = mday

    def __repr__(self):
        return '<Station %s>' % self.sno    

db.create_all()


###
# Routing for your application.
###

body = {
    "code": 0,
    "result": []
}


@app.route('/v1/ubike-station/taipei', methods=['GET'])
def get_station():
    input = request.args.to_dict() 
    if 'lat' not in input.keys() or 'lng' not in input.keys():
        body['code'] = -1
        return jsonify(body)

    elif input['lat'] is None or input['lng'] is None:
        body['code'] = -1
        return jsonify(body)

    latlng = str(input['lat'] + ',' + input['lng'])
    url = 'https://maps.googleapis.com/maps/api/geocode/json?latlng='
    url = url + latlng
    http = urllib3.PoolManager()
    
    try:
        r = http.request('GET',url, timeout = 5.0)
    except Exception as e:
        body['code'] = -3
        return jsonify(body)    
    
    if r.status != 200:
        body['code'] = -3
    else:
        res = json.loads(r.data)
        if res['status'] != 'OK':
            body['code'] = -1
        else:
            country = -1
            county = -1
            country = res["results"][-1]["address_components"][0]["long_name"]
            try:
                county = res["results"][0]["address_components"][4]["long_name"]
            except Exception as e:
                pass
            print country, county
            if country != "Taiwan" or county != "Taipei City":
                body['code'] = -2
            else:
                result = find_stations(input['lat'], input['lng'])
                if result != []:
                    body['code'] = 0
                    body['result'] = result
                else:
                    body['code'] = 1
                    
    return jsonify(body)

###
# Update DB
###

@app.route('/update/stations/', methods=['GET'])
def update_stations():
    data = download_ubike()
    print 'download data'
    for k, v in data['retVal'].iteritems():
        if not db.session.query(Station).filter(Station.sno == v['sno']).count():
            reg = Station(v['sno'], v['sna'], v['lat'], v['lng'], 
                    str(quadkey.from_geo((v['lat'], v['lng']), 17)),  v['mday'])
            db.session.add(reg)
            db.session.commit()

    updated = data['retVal']['0134']['mday']
    return jsonify({'status': 'successed', 'updated': updated})

@app.route('/update/sbi/', methods=['GET'])
def update_sbi():
    data = download_ubike()
    for k, v in data['retVal'].iteritems():
        if not db.session.query(Sbi).filter(Sbi.sno == v['sno']).count():
            reg = Sbi(v['sno'], v['sbi'], v['act'], v['mday'])
            db.session.add(reg)
            db.session.commit()
            print 'add %s' % v['sno']
        else:
            sbi = Sbi.query.filter_by(sno=v['sno']).first()
            print sbi
            sbi.sbi = v['sbi']
            sbi.act = v['act']
            sbi.mday = v['mday']
            db.session.commit()
            print 'update %s: %s' % (v['sno'], v['sbi'])

    updated = data['retVal']['0134']['mday']
    return jsonify({'status': 'successed', 'updated': updated})

###
# The functions below should be applicable to all Flask apps.
###

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
