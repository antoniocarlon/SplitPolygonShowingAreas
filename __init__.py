from __future__ import absolute_import
def classFactory(iface):
	from .plugin import SplitFeaturesOnSteroidsPlugin
	return SplitFeaturesOnSteroidsPlugin(iface)
