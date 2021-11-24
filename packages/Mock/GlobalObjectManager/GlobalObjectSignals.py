from gii.core        import app, signals

signals.register ( 'global_object.added' )
signals.register ( 'global_object.removed' )
signals.register ( 'global_object.renamed' )
# signals.register ( 'global_object.modified' )
