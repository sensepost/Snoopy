import logging
#log = logging.getLogger('snoopy')

from beaker.middleware import SessionMiddleware
from flask import Flask, jsonify, request, redirect, render_template, url_for
from sqlalchemy import distinct, func

from snoopy import config, db, pluginregistry

from snoopy.web import login_required


app = Flask('snoopy')

@app.route('/')
@login_required
def main():
    return render_template('main.html')


@app.route('/login')
def login():
    beaker = request.environ['beaker.session']
    if beaker.has_key('userid'):
        return redirect(url_for('main'))
    else:
        return render_template('login.html')


@app.route('/login', methods=['POST'])
def perform_login_json():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    user = db.User.check_password(username, password)
    if user:
        beaker = request.environ['beaker.session']
        beaker['userid'] = user.id
        beaker.save()
        return jsonify(success=True)
    return jsonify(success=False)


@app.route('/logout')
def logout():
    beaker = request.environ['beaker.session']
    del beaker['userid']
    beaker.save()
    return redirect(url_for('login'))


@app.route('/drone/list', methods=['POST'])
@login_required
def drone_list_json():
    try:
        with db.SessionCtx() as session:
            devlist = session.query(
                db.Probe.monitor, func.count(distinct(db.Probe.device_mac))
            ).group_by(db.Probe.monitor).all()
            devlist = [dict(zip(('devname', 'n_macs'), d)) for d in devlist]
            return jsonify(success=True, drones=devlist)
    except Exception:
        logging.exception('Error getting monitor list:')
        return jsonify(success=False, errors=['Internal error'])


@app.route('/client/list', methods=['POST'])
@login_required
def client_list_json():
    if not request.form.has_key('monitor'):
        logging.error('No monitor specified. This should not happen.')
        return jsonify(success=True, clients=[])
    monitor = request.form['monitor']
    try:
        with db.SessionCtx() as session:
            clients = session.query(
                db.Probe.device_mac,
                func.count(distinct(db.Probe.proximity_session)).label('cnt')
            )
            if monitor != '*':
                clients = clients.filter_by(monitor=monitor)
            clients = clients.group_by(db.Probe.device_mac)
            clients = clients.order_by('cnt DESC').all()
            clients = [{'mac': c[0], 'n_sessions': c[1]} for c in clients]
            return jsonify(success=True, clients=clients)
    except Exception:
        logging.exception('Error getting probed device list:')
        return jsonify(success=False, errors=['Internal error'])


@app.route('/client/data/get', methods=['POST'])
@login_required
def client_data_get():
    mac = request.form.get('mac', None)
    if not mac:
        return jsonify(success=False, errors=['Invalid request'])
    cldata = {}
    for fn, options in pluginregistry.plugins['client-data'].iteritems():
        cldata[options['name']] = dict(title=options['title'], data=fn(mac))
    return jsonify(success=True, client_data=cldata)


@app.route('/plugin/list', methods=['POST'])
@login_required
def plugin_list():
    if request.form.get('group'):
        group = request.form.get('group')
        groupfilter = lambda x: x == group
    else:
        groupfilter = lambda x: True

    plugindata = []
    for group, plugins in pluginregistry.plugins.iteritems():
        if not groupfilter(group):
            continue
        for fn, options in plugins.iteritems():
            if 'js' in options:
                plugindata.append({'jsurl': options['js']})
    return jsonify(success=True, plugins=plugindata)


####################################################


def start():
    config.from_sysargv()
    db.init(None)
    pluginregistry.collect()
    app.wsgi_app = SessionMiddleware(app.wsgi_app, config['beaker'])
    app.config.update(config['flask'])
    app.run(host='0.0.0.0')

if __name__ == '__main__':
    start()
