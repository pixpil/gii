module 'mock_edit'

local QtDialogs = gii.importPythonModule 'gii.qt.dialogs'

function requestString( title, prompt )
	return QtDialogs.requestString( title, prompt )
end

function requestProperty( title, target )
	return QtDialogs.requestProperty( title, target )
end

function requestConfirm( title, msg, level )
	return QtDialogs.requestConfirm( title, msg, level )
end

function alertMessage( title, msg, level )
	return QtDialogs.alertMessage( title, msg, level )
end

function popInfo( title, msg )
	return alertMessage( title, msg or title, 'info' )
end

function popQuestion( title, msg )
	return alertMessage( title, msg or title, 'question' )
end

function popWarning( title, msg )
	return alertMessage( title, msg or title, 'warning' )
end

function popCritical( title, msg )
	return alertMessage( title, msg or title, 'critical' )
end
