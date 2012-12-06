Snoopy.registerPlugin('wigle', function(section, clData) {
    if (!Snoopy.util.loadGoogleMaps()) {
        console.error('Google Maps not (yet) loaded');
        return;
    }

    if (!clData.length) {
        console.debug('No Wigle data received.');
        return;
    }

    var $map = $(document.createElement('div'))
            .attr('id', 'wigle_map')
            .css({ width: '425px', height: '350px', border: '1px solid #abbce6' }),
        mapId='wigle_' + $('.cwin-title', section.parent().parent()).text(),
        markers=[], avg_long=0.0, avg_lat=0.0,
        coords, map, i;

    for (i=0; i < clData.length; i++) {
        coords = clData[i];
        console.debug(coords.lat + ', ' + coords.long + '(' + coords.ssid + ')');
        markers.push(new google.maps.Marker({
            title: coords.ssid + ' (' + Snoopy.util.dateFormat(coords.timestamp) + ')',
            position: new google.maps.LatLng(coords.lat, coords.long)
        }));
        avg_lat += coords.lat;
        avg_long += coords.long;
    }

    avg_lat  /= clData.length;
    avg_long /= clData.length;

    map = new google.maps.Map($map[0], {
        zoom: 6, mapTypeId: google.maps.MapTypeId.ROADMAP,
        center: new google.maps.LatLng(avg_lat, avg_long),
    });

    for (var i=0; i < markers.length; i++) {
        markers[i].setMap(map);
    }

    $('.section-content', section).append($map);
});
