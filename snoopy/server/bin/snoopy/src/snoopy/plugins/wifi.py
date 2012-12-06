# -*- coding: utf-8 -*-

from snoopy import db, pluginregistry


@pluginregistry.add('client-data', 'ssids', 'SSIDs', js='/static/js/ssidlist.js')
def ssid_list(mac):
    with db.SessionCtx() as session:
        query = session.query(
            # SELECT probe_ssid, proximity_session FROM probes
            db.Probe.probe_ssid, db.Probe.proximity_session
        ).filter_by(
            # WHERE device_mac=$mac
            device_mac=mac
        ).group_by(
            # GROUP BY proximity_session, probe_ssid
            db.Probe.proximity_session, db.Probe.probe_ssid
        ).order_by(
            # ORDER BY probe_ssid
            db.Probe.probe_ssid
        )

        results = {}
        for ssid, prox_sess in query.all():
            if not ssid:
                ssid = '[blank ssid]'
            if not ssid or not prox_sess:
                continue
            if ssid not in results:
                results[ssid] = []
            if prox_sess not in results[ssid]:
                results[ssid].append(prox_sess)
        return results
