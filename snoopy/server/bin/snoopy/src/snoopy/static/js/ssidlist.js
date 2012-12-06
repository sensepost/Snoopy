Snoopy.registerPlugin('ssids', function(section, clData) {
    var $outer_ul = $(document.createElement('ul'));
    for (var ssid in clData) {
        if (!clData.hasOwnProperty(ssid)) { continue; }
        var $ps_ul = $(document.createElement('ul')),
            prox_sessions = clData[ssid],
            ssid_i;
        for (ssid_i=0; ssid_i < prox_sessions.length; ssid_i++)
            $ps_ul.append( $(document.createElement('li')).text(prox_sessions[ssid_i]) );
        $outer_ul.append(
            $(document.createElement('li'))
                .text(ssid).append($ps_ul).expander()
        );
    }
    $('.section-content', section).append($outer_ul);
});
