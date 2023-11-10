-- Signalétique

CREATE VIEW {{ schema_geotrek }}.v_signages AS WITH v_signage_tmp AS
    (SELECT e.id,
            {% for lang in MODELTRANSLATION_LANGUAGES %}
                t.published_{{ lang }},
            {% endfor %}
            t.publication_date,
            t.topo_object_id,
            {% for lang in MODELTRANSLATION_LANGUAGES %}
                t.name_{{ lang }},
            {% endfor %}
            {% for lang in MODELTRANSLATION_LANGUAGES %}
                t.description_{{ lang }},
            {% endfor %}
            t.implantation_year,
            t.eid,
            t.code,
            t.printed_elevation,
            t.manager_id,
            {% comment %} t.condition_id, {% endcomment %}
            p.labels AS "Condition",
            t.sealing_id,
            t.access_id,
            t.structure_id,
            t.type_id,
            CONCAT (e.min_elevation, 'm') AS elevation,
            e.geom
        FROM signage_signage t
            left join core_topology e on t.topo_object_id = e.id
            left join signage_signagetype b on t.type_id = b.id
        -- FROM signage_signage t,
        --   signage_signagetype b,
        --   core_topology e
        LEFT JOIN
            (SELECT a.signagecondition_id, b.label AS labels, a.signage_id
                FROM signage_signagecondition b
                JOIN signage_signage_conditions a ON a.signagecondition_id = b.id) p
                ON t.topo_object_id = p.signage_id
        WHERE e.deleted = FALSE )
SELECT a.id,
       e.name AS "Structure",
       f.zoning_city AS "City",
       g.zoning_district AS "District",
       {% for lang in MODELTRANSLATION_LANGUAGES %}
        a.name_{{ lang }} AS "Name {{ lang }}",
       {% endfor %}
       a.code AS "Code",
       b.label AS "Type",
    --    c.label AS "State",
       {% for lang in MODELTRANSLATION_LANGUAGES %}
        a.description_{{ lang }} AS "Description {{ lang }}",
       {% endfor %}
       a.implantation_year AS "Implantation year",
       a.printed_elevation AS "Printed elevation",
       concat('X : ', st_x(st_transform(a.geom,{{ API_SRID }}))::numeric(9,7),
              ' / Y : ', st_y(st_transform(a.geom,{{ API_SRID }}))::numeric(9,7),
              ' ({{ spatial_reference }})') AS "Coordinates",
       d.label AS "Sealing",
       h.organism AS "Manager",
       i.label AS "Access mean",
       {% for lang in MODELTRANSLATION_LANGUAGES %}
           CASE
               WHEN a.published_{{ lang }} IS FALSE THEN 'No'
               WHEN a.published_{{ lang }} IS TRUE THEN 'Yes'
           END AS "Published {{ lang }}",
       {% endfor %}
       a.elevation AS "Elevation",
       a.publication_date AS "Insertion date",
       a.geom
FROM v_signage_tmp a
LEFT JOIN signage_signagetype b ON a.type_id = b.id
LEFT JOIN (SELECT a.signagecondition_id, b.label AS labels, a.signage_id
                FROM signage_signagecondition b
                JOIN signage_signage_conditions a ON a.signagecondition_id = b.id) c
        ON a.id = c.signage_id
-- LEFT JOIN infrastructure_infrastructurecondition c ON a.condition_id = c.id
LEFT JOIN signage_sealing d ON a.sealing_id = d.id
LEFT JOIN authent_structure e ON a.structure_id = e.id
LEFT JOIN infrastructure_infrastructureaccessmean i ON a.access_id = i.id
LEFT JOIN
    (SELECT array_to_string(ARRAY_AGG (b.name ORDER BY b.name), ', ', '_') zoning_city,
            a.id
     FROM
         (SELECT e.id,
                 e.geom
          FROM signage_signage t,
               signage_signagetype b,
               core_topology e
          WHERE t.topo_object_id = e.id
              AND t.type_id = b.id
              AND e.deleted = FALSE ) a
     JOIN zoning_city b ON ST_INTERSECTS (a.geom, b.geom)
     GROUP BY a.id) f ON a.id = f.id
LEFT JOIN
    (SELECT array_to_string(ARRAY_AGG (b.name ORDER BY b.name), ', ', '_') zoning_district,
            a.id
     FROM
         (SELECT e.id,
                 e.geom
          FROM signage_signage t,
               signage_signagetype b,
               core_topology e
          WHERE t.topo_object_id = e.id
              AND t.type_id = b.id
              AND e.deleted = FALSE ) a
     JOIN zoning_district b ON ST_INTERSECTS (a.geom, b.geom)
     GROUP BY a.id) g ON a.id = g.id
LEFT JOIN
    (SELECT organism,
            b.topo_object_id
     FROM common_organism a
     JOIN signage_signage b ON a.id = b.manager_id) h ON a.topo_object_id = h.topo_object_id 
;
