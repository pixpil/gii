from .signals import register

register('app.activate')
register('app.deactivate')

register('app.pre_start')
register('app.start')
register('app.ready')
register('app.close')
register('app.stop')
register('app.chdir')
register('app.command')
register('app.remote')
register('app.asset_scanned')

register('app.update')

register('app.open_url')

register('module.loaded')

register( 'command.new'  )
register( 'command.undo' )
register( 'command.redo' )
register( 'command.clear' )

register('game.pause')
register('game.resume')

register('preview.start')
register('preview.resume')
register('preview.stop')
register('preview.pause')

register('debug.enter')
register('debug.exit')
register('debug.continue')
register('debug.stop')

register('debug.command')
register('debug.info')

register('file.modified')
register('file.removed')
register('file.added')
register('file.moved')

register('module.register')
register('module.override')
register('module.unregister')
register('module.load')
register('module.unload')

register('selection.changed')
register('selection.hint')

register('project.init')
register('project.preload')
register('project.presave')
register('project.load')
register('project.save')

register('project.pre_deploy')
register('project.deploy')
register('project.post_deploy')
register('project.done_deploy')

register('asset.reset')
register('asset.post_import_all')
register('asset.imported_all')
register('asset.index.pre_save')
register('asset.index.save')
register('asset.imported')
register('asset.ready')
register('asset.added')
register('asset.removed')
register('asset.modified')
register('asset.moved')
register('asset.deploy.changed')

register('asset.register')
register('asset.unregister')

