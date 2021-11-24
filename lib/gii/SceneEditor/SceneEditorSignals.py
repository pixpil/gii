from gii.core.signals import register 

register( 'root_group.renamed' )
register( 'root_group.removed' )
register( 'root_group.added' )

register( 'scene.pre_open' )
register( 'scene.update' )
register( 'scene.clear' )
register( 'scene.save' )
register( 'scene.saved' )
register( 'scene.open' )
register( 'scene.close' )
register( 'scene.change' ) #Scene is changed during preview

register( 'scene.modified' )

register( 'entity.added' )
register( 'entity.removed' )
register( 'entity.modified' )
register( 'entity.renamed' )
register( 'entity.gizmo_changed' )
register( 'entity.reorder' )

register( 'entity.visible_changed' )
register( 'entity.pickable_changed' )

register( 'prefab.unlink' )
register( 'prefab.relink' )
register( 'prefab.push' )
register( 'prefab.pull' )

register( 'proto.unlink' )
register( 'proto.relink' )

register( 'component.added' )
register( 'component.removed' )
register( 'component.renamed' )
register( 'component.reordered' )


register( 'animator.start' )
register( 'animator.stop' )

register( 'scene_tool.change' )
register( 'scene_tool_category.update' )
register( 'external_player.start' )
register( 'external_player.stop' )
