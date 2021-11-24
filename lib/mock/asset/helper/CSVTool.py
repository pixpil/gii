import logging
import json
import csv

##----------------------------------------------------------------##
def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
	# csv.py doesn't do Unicode; encode temporarily as UTF-8:
	csv_reader = csv.reader(unicode_csv_data,
													dialect=dialect, **kwargs)
	for row in csv_reader:
		# decode UTF-8 back to Unicode, cell by cell:
		yield [str(cell, 'utf-8') for cell in row]

def utf_8_encoder(unicode_csv_data):
	for line in unicode_csv_data:
		try:
			l = line
			yield l
		except Exception as e:
			yield line

def _checkNumber( v ):
	if not v:
		return None
	try:
		n = float( v )
		return n
	except Exception as e:
		return v

def loadPlainCSV( path ):
	data = []
	with open( path, 'r', encoding='utf-8' ) as fp:
		reader = csv.reader( fp )
		for row in reader:
			data.append( [ _checkNumber( v ) for v in row ] )
	return data

def loadCSVAsDict( path ):
	data = loadPlainCSV( path )
	output = {}
	for row in data:
		k = row[0]
		v = row[1]
		if k:
			if k in output:
				logging.warn( 'duplicated key "%s" in Dict CSV: %s' % ( k , path ) )
			output[ k ] = v
	return output

def loadCSVAsList( path ):
	data = loadPlainCSV( path )
	if not data: return
	output = []
	header = data[ 0 ]
	for row in data[1:]	:
		rowItem = {}
		for i, v in enumerate( row ):
			try:
				key = header[ i ]
				rowItem[ key ] = v
			except Exception as e:
				pass
		output.append( rowItem )
	return output

if __name__ == '__main__':
	from gii.core import AssetManager, AssetLibrary, getProjectPath, app, JSONHelper
	
	data = loadPlainCSV( 'test/test.csv' )
	# data = loadCSVAsList( 'test/test.csv' )
	JSONHelper.trySaveJSON( data, 'test/test_csv.json' )
