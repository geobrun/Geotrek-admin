from django.conf import settings
from django.contrib.gis.db.models.functions import Transform
from django.db.models import F, Prefetch, Q
from django.db.models.aggregates import Count
from django.http import Http404
from django.utils.translation import activate
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework_extensions.cache.decorators import cache_response

from geotrek.api.v2 import filters as api_filters
from geotrek.api.v2 import serializers as api_serializers
from geotrek.api.v2 import viewsets as api_viewsets
from geotrek.api.v2.functions import Length3D
from geotrek.api.v2.renderers import SVGProfileRenderer
from geotrek.api.v2.utils import build_response_from_cache
from geotrek.common.models import Attachment, AccessibilityAttachment
from geotrek.trekking import models as trekking_models


class WebLinkCategoryViewSet(api_viewsets.GeotrekViewSet):
    serializer_class = api_serializers.WebLinkCategorySerializer
    queryset = trekking_models.WebLinkCategory.objects.all()


class TrekViewSet(api_viewsets.GeotrekGeometricViewset):
    filter_backends = api_viewsets.GeotrekGeometricViewset.filter_backends + (
        api_filters.GeotrekTrekQueryParamsFilter,
        api_filters.NearbyContentFilter,
        api_filters.UpdateOrCreateDateFilter,
        api_filters.GeotrekRatingsFilter
    )
    serializer_class = api_serializers.TrekSerializer

    def get_object_cache_key(self, pk):
        """ Extends default cache key with attachments last update """
        last_attachment = self.get_object().attachments.all().order_by('-date_update').first()
        last_attachment_update = last_attachment.date_update.isoformat() if last_attachment else None
        base_key = super().get_object_cache_key(pk)
        return f"{base_key}:{last_attachment_update}"

    def get_queryset(self):
        activate(self.request.GET.get('language'))
        return trekking_models.Trek.objects.existing() \
            .select_related('topo_object') \
            .prefetch_related('topo_object__aggregations', 'accessibilities',
                              Prefetch('attachments',
                                       queryset=Attachment.objects.select_related('license', 'filetype', 'filetype__structure')),
                              Prefetch('attachments_accessibility',
                                       queryset=AccessibilityAttachment.objects.select_related('license')),
                              Prefetch('web_links',
                                       queryset=trekking_models.WebLink.objects.select_related('category'))) \
            .annotate(geom3d_transformed=Transform(F('geom_3d'), settings.API_SRID),
                      length_3d_m=Length3D('geom_3d')) \
            .order_by("name")  # Required for reliable pagination

        return qs

    @cache_response(key_func='object_cache_key_func', timeout='object_cache_timeout')
    def retrieve(self, request, pk=None, format=None):
        """ Return detail view even for unpublished treks that are children of other published treks """
        qs_filtered = self.filter_published_lang_retrieve(request, self.get_queryset())
        trek = get_object_or_404(qs_filtered, pk=pk)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(trek, many=False, context={'request': request})
        return Response(serializer.data)

    def filter_published_lang_retrieve(self, request, queryset):
        """ filter trek by publication language (including parents publication language) """
        qs = queryset
        language = request.GET.get('language', 'all')
        associated_published_fields = [f.name for f in qs.model._meta.get_fields() if f.name.startswith('published')]

        if language == 'all':
            # no language specified. Check for all.
            q = Q()
            for lang in settings.MODELTRANSLATION_LANGUAGES:
                field_name = 'published_{}'.format(lang)
                if field_name in associated_published_fields:
                    field_name_parent = 'trek_parents__parent__published_{}'.format(lang)
                    q |= Q(**{field_name: True}) | Q(**{field_name_parent: True})
            qs = qs.filter(q)
        else:
            # one language is specified
            field_name = 'published_{}'.format(language)
            field_name_parent = 'trek_parents__parent__published_{}'.format(language)
            qs = qs.filter(Q(**{field_name: True}) | Q(**{field_name_parent: True}))
        return qs.distinct()

    @action(detail=True, url_name="dem")
    def dem(self, request, pk):
        trek = self.get_object()
        trek_date_update = trek.get_date_update().strftime('%y%m%d%H%M%S%f')
        json_lookup = f"altimetry_dem_area_{trek.pk}_{trek_date_update}"
        return build_response_from_cache(json_lookup, trek.get_elevation_area, content_type="application/json")

    @action(detail=True, url_name="profile", renderer_classes=api_viewsets.GeotrekGeometricViewset.renderer_classes + [SVGProfileRenderer, ])
    def profile(self, request, pk):
        trek = self.get_object()
        trek_date_update = trek.get_date_update().strftime('%y%m%d%H%M%S%f')
        if request.accepted_renderer.format == 'svg':
            json_lookup = f"altimetry_profile_{trek.pk}_{trek_date_update}_svg"
            return build_response_from_cache(json_lookup, data_func=trek.get_elevation_profile_and_limits, content_type="image/svg+xml")
        json_lookup = f"altimetry_profile_{trek.pk}_{trek_date_update}_formatted"
        return build_response_from_cache(json_lookup, data_func=trek.get_formatted_elevation_profile_and_limits, content_type="application/json")


class TourViewSet(TrekViewSet):
    serializer_class = api_serializers.TourSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.annotate(count_children=Count('trek_children'))\
            .filter(count_children__gt=0)
        return qs


class PracticeViewSet(api_viewsets.GeotrekViewSet):
    filter_backends = api_viewsets.GeotrekViewSet.filter_backends + (api_filters.TrekRelatedPortalFilter,)
    serializer_class = api_serializers.PracticeSerializer
    queryset = trekking_models.Practice.objects.all()

    @cache_response(key_func='object_cache_key_func', timeout='object_cache_timeout')
    def retrieve(self, request, pk=None, format=None):
        # Allow to retrieve objects even if not visible in list view
        elem = get_object_or_404(trekking_models.Practice, pk=pk)
        serializer = api_serializers.PracticeSerializer(elem, many=False, context={'request': request})
        return Response(serializer.data)


class TrekRatingScaleViewSet(api_viewsets.GeotrekViewSet):
    filter_backends = api_viewsets.GeotrekViewSet.filter_backends + (api_filters.GeotrekRatingScaleFilter, )
    serializer_class = api_serializers.TrekRatingScaleSerializer
    queryset = trekking_models.RatingScale.objects \
        .order_by('pk')  # Required for reliable pagination


class TrekRatingViewSet(api_viewsets.GeotrekViewSet):
    filter_backends = api_viewsets.GeotrekViewSet.filter_backends + (
        api_filters.GeotrekRatingFilter,
        api_filters.TrekRelatedPortalFilter,
    )
    serializer_class = api_serializers.TrekRatingSerializer
    queryset = trekking_models.Rating.objects \
        .order_by('order', 'name', 'pk')  # Required for reliable pagination


class NetworkViewSet(api_viewsets.GeotrekViewSet):
    filter_backends = api_viewsets.GeotrekViewSet.filter_backends + (api_filters.TrekRelatedPortalFilter,)
    serializer_class = api_serializers.NetworkSerializer
    queryset = trekking_models.TrekNetwork.objects.all()

    @cache_response(key_func='object_cache_key_func', timeout='object_cache_timeout')
    def retrieve(self, request, pk=None, format=None):
        # Allow to retrieve objects even if not visible in list view
        elem = get_object_or_404(trekking_models.TrekNetwork, pk=pk)
        serializer = api_serializers.NetworkSerializer(elem, many=False, context={'request': request})
        return Response(serializer.data)


class DifficultyViewSet(api_viewsets.GeotrekViewSet):
    filter_backends = api_viewsets.GeotrekViewSet.filter_backends + (api_filters.TrekRelatedPortalFilter,)
    serializer_class = api_serializers.TrekDifficultySerializer
    queryset = trekking_models.DifficultyLevel.objects.all()

    @cache_response(key_func='object_cache_key_func', timeout='object_cache_timeout')
    def retrieve(self, request, pk=None, format=None):
        # Allow to retrieve objects even if not visible in list view
        elem = get_object_or_404(trekking_models.DifficultyLevel, pk=pk)
        serializer = api_serializers.TrekDifficultySerializer(elem, many=False, context={'request': request})
        return Response(serializer.data)


class POIViewSet(api_viewsets.GeotrekGeometricViewset):
    filter_backends = api_viewsets.GeotrekGeometricViewset.filter_backends + (
        api_filters.GeotrekPOIFilter,
        api_filters.NearbyContentFilter,
        api_filters.UpdateOrCreateDateFilter
    )
    serializer_class = api_serializers.POISerializer
    queryset = trekking_models.POI.objects.existing() \
        .select_related('topo_object', 'type', ) \
        .prefetch_related('topo_object__aggregations',
                          Prefetch('attachments',
                                   queryset=Attachment.objects.select_related('license', 'filetype', 'filetype__structure'))) \
        .annotate(geom3d_transformed=Transform(F('geom_3d'), settings.API_SRID)) \
        .order_by('pk')  # Required for reliable pagination

    def get_object_cache_key(self, pk):
        """ Extends default cache key with attachments last update """
        last_attachment = self.get_object().attachments.all().order_by('-date_update').first()
        last_attachment_update = last_attachment.date_update.isoformat() if last_attachment else None
        base_key = super().get_object_cache_key(pk)
        return f"{base_key}:{last_attachment_update}"


class POITypeViewSet(api_viewsets.GeotrekViewSet):
    serializer_class = api_serializers.POITypeSerializer
    queryset = trekking_models.POIType.objects.all()


class AccessibilityViewSet(api_viewsets.GeotrekViewSet):
    filter_backends = api_viewsets.GeotrekViewSet.filter_backends + (api_filters.TrekRelatedPortalFilter,)
    serializer_class = api_serializers.AccessibilitySerializer
    queryset = trekking_models.Accessibility.objects.all()


class AccessibilityLevelViewSet(api_viewsets.GeotrekViewSet):
    filter_backends = api_viewsets.GeotrekViewSet.filter_backends + (api_filters.TrekRelatedPortalFilter,)
    serializer_class = api_serializers.AccessibilityLevelSerializer
    queryset = trekking_models.AccessibilityLevel.objects.all()


class RouteViewSet(api_viewsets.GeotrekViewSet):
    filter_backends = api_viewsets.GeotrekViewSet.filter_backends + (api_filters.TrekRelatedPortalFilter,)
    serializer_class = api_serializers.RouteSerializer
    queryset = trekking_models.Route.objects.all()

    @cache_response(key_func='object_cache_key_func', timeout='object_cache_timeout')
    def retrieve(self, request, pk=None, format=None):
        # Allow to retrieve objects even if not visible in list view
        elem = get_object_or_404(trekking_models.Route, pk=pk)
        serializer = api_serializers.RouteSerializer(elem, many=False, context={'request': request})
        return Response(serializer.data)


class ServiceTypeViewSet(api_viewsets.GeotrekViewSet):
    serializer_class = api_serializers.ServiceTypeSerializer
    queryset = trekking_models.ServiceType.objects.all().order_by('pk')

    @cache_response(key_func='object_cache_key_func', timeout='object_cache_timeout')
    def retrieve(self, request, pk=None, format=None):
        # Allow to retrieve objects even if not visible in list view
        elem = get_object_or_404(trekking_models.ServiceType, pk=pk)
        serializer = api_serializers.ServiceTypeSerializer(elem, many=False, context={'request': request})
        return Response(serializer.data)


class ServiceViewSet(api_viewsets.GeotrekGeometricViewset):
    filter_backends = api_viewsets.GeotrekGeometricViewset.filter_backends + (api_filters.NearbyContentFilter, api_filters.UpdateOrCreateDateFilter, api_filters.GeotrekServiceFilter)
    serializer_class = api_serializers.ServiceSerializer
    queryset = trekking_models.Service.objects.all() \
        .select_related('topo_object', 'type', ) \
        .prefetch_related('topo_object__aggregations',
                          Prefetch('attachments',
                                   queryset=Attachment.objects.select_related('license', 'filetype', 'filetype__structure')),) \
        .annotate(geom3d_transformed=Transform(F('geom_3d'), settings.API_SRID)) \
        .order_by('pk')
