# -*- coding: utf-8 -*-

from snoopy import db, pluginregistry


@pluginregistry.add('client-data', 'wigle', 'Wigle', js='/static/js/wigle.js')
def wigle(mac):
    results = []
    with db.SessionCtx() as session:
        query = session.query(db.Probe, db.Wigle).\
                    filter(
                        db.Probe.device_mac == mac,
                        db.Probe.probe_ssid == db.Wigle.ssid
                    ).\
                    group_by(db.Probe.device_mac, db.Probe.probe_ssid).\
                    order_by(db.Probe.timestamp)
        for probe_row, wigle_row in query:
            if wigle_row.gps_long is None or wigle_row.gps_lat is None:
                continue
            ssid = wigle_row.ssid
            if not ssid:
                ssid = '[unknown]'
            results.append({
                'long': float(wigle_row.gps_long),
                'lat': float(wigle_row.gps_lat),
                'ssid': wigle_row.ssid,
                'timestamp': str(probe_row.timestamp)
            })
    return results
