import os.path
import logging

from gii.core import AssetManager, AssetLibrary, getProjectPath, app, JSONHelper

import re
import xlrd

##----------------------------------------------------------------##
def cellValue( cell ):
	if cell.ctype == xlrd.XL_CELL_BOOLEAN:
		return cell.value == 1
	elif cell.ctype == xlrd.XL_CELL_EMPTY:
		return None
	else:
		return cell.value

def convertSheetToData( sheet ):
	def _procKey( k ):
		if not k: return k, None
		if k.startswith( '%' ): #localizable
			key = k[1:]
			return key, 'localizable'
		else:
			return k, False

	name = sheet.name
	mo = re.match( '(\w+)@(\w+)', name )
	if not mo: return False, None, None
	sheetId  = mo.group(1)
	typeName = mo.group(2)
	metaData = {
		'name' : sheetId,
		'type' : typeName,
	}

	if typeName == 'list':
		data = []
		cols = sheet.ncols
		rows = sheet.nrows
		if rows<2: return False
		keys = []
		keyMetas = []
		for cell in sheet.row( 0 ):
			key, meta = _procKey( cell.value )
			keys.append( key )
			keyMetas.append( meta )

		for row in range( 1, rows ):
			cell0 = sheet.cell( row, 0 )
			k  = cellValue( cell0 )
			if isinstance( k, str ) and k.startswith( '//' ): continue #skip comment line
			rowData = {}
			for i, key in enumerate( keys ):
				if key:
					cell = sheet.cell( row, i )
					rowData[key] = cellValue( cell )
			data.append( rowData )
		
		metaData.update({
			'keys' : keys,
			'keyMeta' :keyMetas
		})
		return sheetId, data, metaData

	elif typeName == 'vlist':
		data = []
		cols = sheet.ncols
		rows = sheet.nrows
		if cols<2: return False
		keys = []
		keyMetas = []
		for cell in sheet.col( 0 ):
			key, meta = _procKey( cell.value )
			keys.append( key )
			keyMetas.append( meta )

		for col in range( 1, cols ):
			cell0 = sheet.cell( 0, col )
			k  = cellValue( cell0 )
			if isinstance( k, str ) and k.startswith( '//' ): continue #skip comment line
			colData = {}
			for i, key in enumerate( keys ):
				if key:
					cell = sheet.cell( i, col )
					colData[key] = cellValue( cell )
			data.append( colData )

		metaData.update({
			'keys' : keys,
			'keyMeta' :keyMetas
		})
		return sheetId, data, metaData

	elif typeName == 'dict':
		data = {}
		comments = {}
		rows = sheet.nrows
		cols = sheet.ncols
		if cols<2:
			logging.warn( 'KV table columns must >= 2' )
		sequence = []
		for row in range( 0, rows ):
			key = sheet.cell( row, 0 ).value
			if not key: continue
			if isinstance( key, str ) and key.startswith( '//' ): continue #skip comment line
			value = sheet.cell( row, 1 ).value
			if cols > 2:
				comment = sheet.cell( row, 2 ).value
			else:
				comment = None
			if key in data:
				logging.warn( 'skip duplicated key: %s' % key.encode('utf-8') )
				continue
			data[ key ] = value
			comments[ key ] = comment
			sequence.append( key )
		metaData.update({
			'comment' :comments,
			'sequence' : sequence
		})
		return sheetId, data, metaData
	
	elif typeName == 'raw':
		data = []
		cols = sheet.ncols
		rows = sheet.nrows
		for row in range( rows ):
			cell0 = sheet.cell( row, 0 )
			k  = cellValue( cell0 )
			rowData = []
			for col in range( cols ):
				cell = sheet.cell( row, col )
				rowData.append( cellValue( cell ) )
			data.append( rowData )
		return sheetId, data, metaData

def convertWorkbookToData( workbook ):
	bookData = {}
	bookMetaData = {}
	for sheet in workbook.sheets():
		sheetData = convertSheetToData( sheet ) 
		if sheetData:
			( id, data, metadata )= sheetData
			if not isinstance( id, str ): continue
			if id in bookData:
				logging.warn( 'skip duplicated sheet id: %s' % id.encode('utf-8') )
				continue
			bookData[ id ] = data
			bookMetaData[ id ] = metadata
	return bookData, bookMetaData

##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

##----------------------------------------------------------------##
class DataXLSAssetManager(AssetManager):
	def getName(self):
		return 'asset_manager.data_xls'

	def getVersion(self):
		return '1.001'

	def acceptAssetFile(self, filepath):
		if not os.path.isfile(filepath): return False		
		name, ext = os.path.splitext(filepath)
		if not ext in ['.xls']: return False
		return True

	def importAsset(self, node, reload = False ):
		if node.isVirtual(): return

		#JOB: convert xls into json
		workbook = xlrd.open_workbook( node.getAbsFilePath() )
		if not workbook:
			logging.warn( 'excel version not supported for %s' % node.getFilePath() )
			return False

		data, metadata = convertWorkbookToData( workbook )
		if not data:
			logging.warn( 'no data converted from xls: %s' % node.getFilePath() )
			return False
		cachePath = node.getCacheFile( 'data' )

		if not JSONHelper.trySaveJSON( data, cachePath ):
			logging.warn( 'failed saving xls data: %s' % cachePath )
			return False

		metaCachePath = node.getCacheFile( 'meta_data' )
		if not JSONHelper.trySaveJSON( metadata, metaCachePath ):
			logging.warn( 'failed saving xls metadata: %s' % metaCachePath )
			return False

		node.assetType = 'data_xls'
		node.setObjectFile( 'data', cachePath )
		node.setObjectFile( 'meta_data', metaCachePath )
		node.groupType = 'package'
		for id, sheet in list(data.items()):
			if isinstance( id, str ):
				node.affirmChildNode( id, 'data_sheet', manager = self )
		return True

	def editAsset(self, node):
		if node.isVirtual():
			return self.editAsset( node.getParent() )
		node.openInSystem()

DataXLSAssetManager().register()
AssetLibrary.get().setAssetIcon( 'data_xls',   'data' )
AssetLibrary.get().setAssetIcon( 'data_sheet', 'data' )

