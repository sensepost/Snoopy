# -*- coding: utf-8 -*-

from snoopy import db, pluginregistry


@pluginregistry.add('client-data', 'gpsmovs', 'GPS Movements', js='/static/js/gpsmovs.js')
def gps_movements(mac):
    results = {}
    with db.SessionCtx() as session:
        query = session.query(db.Probe, db.GpsMovement).\
                    filter(
                        db.Probe.device_mac == mac,
                        db.Probe.monitor == db.GpsMovement.monitor,
                        db.GpsMovement.timestamp >= db.Probe.timestamp-5,
                        db.GpsMovement.timestamp <= db.Probe.timestamp+5,
                    ).\
                    order_by(db.GpsMovement.run_id, db.GpsMovement.timestamp)
        for probe_row, gpsmov_row in query:
            if gpsmov_row.run_id not in results:
                results[gpsmov_row.run_id] = []
            results[gpsmov_row.run_id].append({
                'long': float(gpsmov_row.gps_long),
                'lat': float(gpsmov_row.gps_lat),
                'accuracy': float(gpsmov_row.accuracy),
		'timestamp': str(gpsmov_row.timestamp)
            })
    return results
