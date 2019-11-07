from numpy import genfromtxt
import numpy as np
import ephem
from urllib.request import urlopen
import math
from bs4 import BeautifulSoup


def readconfig(directory,_file):
    data=genfromtxt(directory+_file,str)
    gg={}
    for i in data:
        try:
            gg[i[0]]=eval(i[1])
        except:
            gg[i[0]]=i[1]
    return gg


def isInt(i):
	try:
		ret = int(i)
		return True
	except:
		return False

def isFloat(i):
	try:
		ret = float(i)
		return True
	except:
		return False

def floatNone(i):
    if i is not None:
        try:
            return float(i)
        except:
            return 0.0
    else:
        return None

def rotate(footprint, angle):
    #footprint is a list of vertices points
    #   vertice points = [ra, dec]

    # angle is the pos_angle of the pointing

    if angle is None:
        return footprint

    rot_footprint = []
    angle = angle * math.pi/180.

    for p in footprint:
        x, y = p[0], p[1]
        r = math.sqrt(x*x + y*y)
        if x < 0:
            r = (-1.0)*r
        theta = math.atan2(y, x)-angle
        new_x = r*math.cos(theta)
        new_y = r*math.sin(theta)
        rot_footprint.append([new_x, new_y])

    return rot_footprint

def project(footprint, _ra, _dec):
        #footprint is a list of vertices points
        #   vertice points = [ra, dec]

        #_ra and _dec are the translated coordinates

        proj_footprint = []
        print(_ra, _dec)
        for p in footprint:
            print(p[0], p[1])
            if _dec >= 89:
                cosdec = 1
            else:
                cosdec = math.cos(math.radians(_dec))
            if p[0]+_ra > 360:
                  ra = 360 - (p[0]/cosdec) +_ra
            elif p[0]+_ra < 0:
                  ra = 360 + (p[0]/cosdec)+_ra
            else:
                ra = (p[0]/cosdec) + _ra

            if p[1]+_dec > 90:
                #ra = (ra + 180) % 360
                print("p[1] + dec > 90")
                dec = 90 - p[1]+_dec

            if p[1]+_dec < -90:
                #ra = (ra + 180) % 360
                print("p[1]+dec < -90")
                dec = -90 + p[1] + _dec
            else:
                print("else")
                dec = p[1] + _dec

            print(ra, dec)

            proj_footprint.append([ra, dec])
        return proj_footprint


def polygons2footprints(polygons):
    #split list of poly corners into ra list and dec list
    footprints= []
    for polygon in polygons:
        if type(polygon[0]) != list:
            polygon = [l.tolist() for l in polygon]
        footprints.append({'polygon':polygon})
    return footprints


def sanatize_footprint_ccds(ccds):
	footprint_ccds = []
	for footprint in ccds:
		sanitized = footprint.strip('POLYGON ').strip(')(').split(',')
		polygon = []
		for vertex in sanitized:
			obj = vertex.split()
			ra = float(obj[0])
			dec = float(obj[1])
			polygon.append([ra,dec])
		footprint_ccds.append(polygon)
	return footprint_ccds


def sanatize_pointing(p):
    ra = float(p.split('(')[1].split(')')[0].split()[0])
    dec = float(p.split('(')[1].split(')')[0].split()[1])
    return ra,dec


def ra_dec_to_uvec(ra, dec):
    phi = np.deg2rad(90 - dec)
    theta = np.deg2rad(ra)
    x = np.cos(theta) * np.sin(phi)
    y = np.sin(theta) * np.sin(phi)
    z = np.cos(phi)
    return x, y, z


def uvec_to_ra_dec(x, y, z):
    r = np.sqrt(x**2 + y ** 2 + z ** 2)
    x /= r
    y /= r
    z /= r
    theta = np.arctan2(y, x)
    phi = np.arccos(z)
    dec = 90 - np.rad2deg(phi)
    if theta < 0:
        ra = 360 + np.rad2deg(theta)
    else:
        ra = np.rad2deg(theta)
    return ra, dec


def x_rot(theta_deg):
    theta = np.deg2rad(theta_deg)
    return np.matrix([
        [1, 0, 0],
        [0, np.cos(theta), -np.sin(theta)],
        [0, np.sin(theta), np.cos(theta)]
    ])


def y_rot(theta_deg):
    theta = np.deg2rad(theta_deg)
    return np.matrix([
        [np.cos(theta), 0, np.sin(theta)],
        [0, 1, 0],
        [-np.sin(theta), 0, np.cos(theta)]
    ])


def z_rot(theta_deg):
    theta = np.deg2rad(theta_deg)
    return np.matrix([
        [np.cos(theta), -np.sin(theta), 0],
        [np.sin(theta), np.cos(theta), 0],
        [0, 0, 1]
    ])


def project_footprint(footprint, ra, dec, pos_angle):
    if pos_angle is None:
        pos_angle = 0.0

    footprint_zero_center_ra = np.asarray([pt[0] for pt in footprint])
    footprint_zero_center_dec = np.asarray([pt[1] for pt in footprint])
    footprint_zero_center_uvec = ra_dec_to_uvec(footprint_zero_center_ra, footprint_zero_center_dec)
    footprint_zero_center_x, footprint_zero_center_y, footprint_zero_center_z = footprint_zero_center_uvec
    proj_footprint = []
    for idx in range(footprint_zero_center_x.shape[0]):
        vec = np.asarray([footprint_zero_center_x[idx], footprint_zero_center_y[idx], footprint_zero_center_z[idx]])
        new_vec = vec @ x_rot(-pos_angle) @ y_rot(dec) @ z_rot(-ra)
        new_x, new_y, new_z = new_vec.flat
        pt_ra, pt_dec = uvec_to_ra_dec(new_x, new_y, new_z)
        proj_footprint.append([pt_ra, pt_dec])
    return proj_footprint

def getDataFromTLE(datetime, tleLatOffset=0, tleLonOffset=0.21):
    # Get TLE and parse
    url = "https://celestrak.com/satcat/tle.php?CATNR=33053"
    data = urlopen(url)
    tle_raw=data.read()
    clean_tle = ''.join(BeautifulSoup(tle_raw, "html.parser").stripped_strings)
    tle_obj = clean_tle.split('\r\n')

    # Print age of TLE
    year = "20"+tle_obj[1][18:20]
    day = tle_obj[1][20:32]
    #print("\nTLE most recently updated "+year+"DOY"+ day)
    
    # Create spacecraft instance
    Fermi = ephem.readtle(tle_obj[0],tle_obj[1],tle_obj[2])
    
    # Create observer
    observer_Fermi = ephem.Observer()
    observer_Fermi.lat = '0'
    observer_Fermi.long = '0'
    
    # Initialize lists
    lat = []
    lon = []
    elevation = []
    
    # Iterate through time; compute predicted locations
    observer_Fermi.date = ephem.date(datetime)
    Fermi.compute(observer_Fermi)
    lat.append(np.degrees(Fermi.sublat.znorm))
    lon.append(np.degrees(Fermi.sublong.norm))
    elevation.append(Fermi.elevation)
    # Correct for inaccuracy
    lon = np.array(lon) - tleLonOffset
    lat = np.array(lat) - tleLatOffset
    
    if len(lon) == 1: # Return single value instead of array if length is 1
        lon = lon[0]
        lat = lat[0]
        elevation = elevation[0]
    
    return lon, lat, elevation

# convert degrees to deg:amin:asec
def deg2dm(deg):
    sign = np.sign(deg)
    deg = np.abs(deg)
    d = np.floor(deg)
    m = (deg - d) * 60
    return int(sign*d), m

def getGeoCenter(datetime, lon, lat):
    # Define the observer to be at the location of the spacecraft
    observer = ephem.Observer()

    # Convert the longitude to +E (-180 to 180)
    if lon > 180:
       lon = (lon % 180) - 180

    lon_deg, lon_min = deg2dm(lon)
    lat_deg, lat_min = deg2dm(lat)

    lon_string = '%s:%s' % (lon_deg, lon_min)
    lat_string = '%s:%s' % (lat_deg, lat_min)

    observer.lon = lon_string
    observer.lat = lat_string
    
    # Set the time of the observations
    observer.date = ephem.date(datetime)
    
    # Get the ra and dec (in radians) of the point in the sky at altitude = 90 (directly overhead)
    ra_zenith_radians, dec_zenith_radians = observer.radec_of('0', '90')
    
    # convert the ra and dec to degrees
    ra_zenith = np.degrees(ra_zenith_radians)
    dec_zenith = np.degrees(dec_zenith_radians)
    
    ra_geocenter =  (ra_zenith+180) % 360
    dec_geocenter = -1 * dec_zenith
    
    return ra_geocenter, dec_geocenter
    
def getearthsatpos(datetime):
    tleLonOffset=0.21
    tleLatOffset = 0

    lon, lat, elevation= getDataFromTLE(datetime, tleLatOffset=tleLatOffset, tleLonOffset=tleLonOffset)

    # Get the geo center coordinates in ra and dec
    ra_geocenter, dec_geocenter = getGeoCenter(datetime, lon, lat)

    EARTH_RADIUS = 6378.140 * 1000 #in meters
    dtor = math.pi/180
    elev = elevation + EARTH_RADIUS
    earthsize_rad = np.arcsin(EARTH_RADIUS/elev)/dtor

    return ra_geocenter,dec_geocenter, earthsize_rad

def makeEarthContour(ra,dec,radius):
    thetas = np.linspace(0, -2*np.pi, 200)
    ras = radius * np.cos(thetas)
    decs = radius * np.sin(thetas)
    contour = np.c_[ras,decs]
    Earthcont = project_footprint(contour, ra, dec, 0)
    return Earthcont