from django.urls import path, converters, register_converter
from mapentity.registry import MapEntityOptions

from . import views

class LangConverter(converters.StringConverter):
    regex = '[a-z]{2}'


register_converter(LangConverter, 'lang')

app_name = 'common'
urlpatterns = [
    path('api/settings.json', views.JSSettings.as_view(), name='settings_json'),
    path('tools/extents/', views.CheckExtentsView.as_view(), name='check_extents'),
    path('commands/import-update.json', import_update_json, name='import_update_json'),
    path('commands/import', views.import_view, name='import_dataset'),
    path('commands/sync', views.SyncRandoRedirect.as_view(), name='sync_randos'),
    path('commands/syncview', views.SyncRandoView.as_view(), name='sync_randos_view'),
    path('commands/statesync/', views.sync_update_json, name='sync_randos_state'),
    path('api/<lang:lang>/themes.json', views.ThemeViewSet.as_view({'get': 'list'}), name="themes_json"),
]


class PublishableEntityOptions(MapEntityOptions):
    document_public_view = views.DocumentPublic
    document_public_booklet_view = views.DocumentBookletPublic
    markup_public_view =views.MarkupPublic

    def scan_views(self, *args, **kwargs):
        """ Adds the URLs of all views provided by ``PublishableMixin`` models.
        """
        views = super().scan_views(*args, **kwargs)
        publishable_views = [
            path('api/<lang:lang>/{name}s/<int:pk>/<slug:slug>_booklet.pdf'.format(name=self.modelname),
                 self.document_public_booklet_view.as_view(model=self.model),
                 name="%s_booklet_printable" % self.modelname),
            path('api/<lang:lang>/{name}s/<int:pk>/<slug:slug>.pdf'.format(name=self.modelname),
                 self.document_public_view.as_view(model=self.model),
                 name="%s_printable" % self.modelname),
            path('api/<lang:lang>/{name}s/<int:pk>/<slug:slug>.html'.format(name=self.modelname),
                 self.markup_public_view.as_view(model=self.model)),
        ]
        return publishable_views + views
