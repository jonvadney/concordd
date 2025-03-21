import flask
import json
import logging
import time;

LOG = logging.getLogger('api')
CONTROLLER = None
app = flask.Flask('concord232')
LOG.info("API Code Loaded")

def show_zone(zone):
    return {
        'partition': zone['partition_number'],
        'area': zone['area_number'],
        'group': zone['group_number'],
        'number': zone['zone_number'],
        'name': zone['zone_text'],
        'state': zone['zone_state'],
        'type': zone['zone_type'],
        #'bypassed': zone.bypassed,
        #'condition_flags': zone.condition_flags,
        #'type_flags': zone.type_flags,
    }


def show_partition(partition):
    return {
        'number': partition['partition_number'],
        'area': partition['area_number'],
        'arming_level': partition['arming_level'],
        'arming_level_code': partition['arming_level_code'],
        'partition_text': partition['partition_text'],
        'zones': sum(z['partition_number'] == partition['partition_number'] for z in CONTROLLER.get_zones().values()),


    }

@app.route('/panel')
def index_panel():
    try:
        result = json.dumps({
            'panel': CONTROLLER.get_panel()
            })
        return flask.Response(result,
                              mimetype='application/json')
    except Exception as e:
        LOG.exception('Failed to index zones')

@app.route('/zones')
def index_zones():
    try:
        zones = CONTROLLER.get_zones()
        result = json.dumps({
            'zones': [show_zone(zone) for zone in zones.values()]})
        return flask.Response(result,
                              mimetype='application/json')
    except Exception as e:
        LOG.exception('Failed to index zones')




@app.route('/partitions')
def index_partitions():
    try:
        partitions = CONTROLLER.get_partitions()
        result = json.dumps({
            'partitions': [show_partition(partition)
                           for partition in partitions.values()]})
        return flask.Response(result,
                              mimetype='application/json')
    except Exception as e:
        LOG.exception('Failed to index partitions')


@app.route('/command')
def command():
    args = flask.request.args
    if args.get('cmd') == 'arm':
        option = args.get('option')
        if args.get('level') == 'stay':
            CONTROLLER.arm_stay(option)
        elif args.get('level') == 'away':
            CONTROLLER.arm_away(option)
    elif args.get('cmd') == 'disarm':
        CONTROLLER.disarm(args.get('master_pin'))
    elif args.get('cmd') == 'keys':
        CONTROLLER.send_keys(args.get('keys'),args.get('group'))
    return flask.Response()

@app.route('/version')
def get_version():
    return flask.Response(json.dumps({'version': '1.1'}),
                          mimetype='application/json')

@app.route('/equipment')
def get_equipment():
    CONTROLLER.refresh()
    return flask.Response()    


@app.route('/all_data')
def get_all_data():
    CONTROLLER.refresh
    return flask.Response()    
