from numpy import genfromtxt

import math

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
        theta = math.atan(y/x)-angle
        new_x = r*math.cos(theta)
        new_y = r*math.sin(theta)
        rot_footprint.append([new_x, new_y])

    return rot_footprint

def project(footprint, _ra, _dec):
        #footprint is a list of vertices points
        #   vertice points = [ra, dec]

        #_ra and _dec are the translated coordinates

        proj_footprint = []
        for p in footprint:
            if p[0]+_ra > 360:
                  ra = 360 - p[0]/math.cos(math.radians(_dec))+_ra
            elif p[0]+_ra < 0:
                  ra = 360 + p[0]/math.cos(math.radians(_dec))+_ra
            else:
                  ra = p[0]/math.cos(math.radians(_dec)) + _ra

            if p[1]+_dec > 90:
                dec = 90 - p[1]+_dec
            elif p[1]+_dec < -90:
                dec = -90 + p[1] + _dec
            else:
                  dec = p[1] + _dec

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
	ra = float(p.split('POINT(')[1].split(')')[0].split()[0])
	dec = float(p.split('POINT(')[1].split(')')[0].split()[1])
	return ra,dec

