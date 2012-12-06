Snoopy.registerPlugin('gpsmovs', function(section, clData) {
    if (!Snoopy.util.loadGoogleMaps()) {
        console.error('Google Maps not (yet) loaded');
        return;
    }

    var $outer_ul = $(document.createElement('ul'));
    for (var runId in clData) {
        if (!clData.hasOwnProperty(runId)) { continue; }
        var $map = $(document.createElement('div'))
                .attr('id', 'map_' + runId)
                .css({ width: '425px', height: '350px', border: '1px solid #abbce6' }),
            coordList=clData[runId],
            markers=[], path=[], avg_long=0.0, avg_lat=0.0,
            red=$.Color('red'), green=$.Color('green'), mCol=$.Color(),
            minTimestamp=9999999999, maxTimestamp=0,
            coords, coords_i, latlng, map;

        if (!coordList.length) { continue; }

        for (coords_i=0; coords_i < coordList.length; coords_i++) {
            coords = coordList[coords_i];

            if (coords.timestamp < minTimestamp) { minTimestamp = coords.timestamp; }
            if (coords.timestamp > maxTimestamp) { maxTimestamp = coords.timestamp; }

            mCol = mCol
                .saturation(1.0)
                .lightness(0.5)
                .hue(Math.round( (green.hue()-red.hue()) * (coords.accuracy / 100.0) ));

            latlng = new google.maps.LatLng(coords.lat, coords.long);
            markers.push(new google.maps.Marker({
                icon: {
                    path: google.maps.SymbolPath.CIRCLE,
                    scale: 4,
                    strokeColor: mCol.toRgbaString()
                },
                title: Snoopy.util.dateFormat(coords.timestamp) + ' (' + coords.accuracy + '%)',
                position: latlng
            }));
            path.push(latlng);
            avg_lat += coords.lat;
            avg_long += coords.long;
        }

        avg_lat  /= coordList.length;
        avg_long /= coordList.length;

        map = new google.maps.Map($map[0], {
            zoom: 18, mapTypeId: google.maps.MapTypeId.ROADMAP,
            center: new google.maps.LatLng(avg_lat, avg_long),
        });

        for (var i=0; i < markers.length; i++) {
            markers[i].setMap(map);
        }

        new google.maps.Polyline({
            clickable: false,
            icons: [{
                icon: {
                    path: google.maps.SymbolPath.FORWARD_CLOSED_ARROW,
                    strokeColor: '#666',
                    strokeWeight: 1.0
                },
                repeat: '150px',
                scale: 0.2
            }],
            map: map,
            path: path,
            strokeColor: '#abbce6'
        });

        $outer_ul.append(
            $(document.createElement('li'))
                .text(Snoopy.util.periodFormat(minTimestamp, maxTimestamp))
                .append($map)
        );
    }
    if ($outer_ul.children().length) {
        $('.section-content', section).append($outer_ul);
    }
});
