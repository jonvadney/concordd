try:
    import ConfigParser as configparser
except ImportError:
    import configparser
from datetime import datetime
import dbus
import sys
import os
import time
import traceback

is_py2 = sys.version[0] == '2'
if is_py2:
    import Queue as Queue
else:
    import queue as Queue

PANEL_TYPES = {
    0x14: "Concord",
    0x0b: "Concord Express",
    0x1e: "Concord Express 4",
    0x0e: "Concord Euro",

    0x0d: "Advent Commercial Fire 250",
    0x0f: "Advent Home Navigator 132",
    0x10: "Advent Commercial Burg 250",
    0x11: "Advent Home Navigator 250",
    0x15: "Advent Commercial Burg 500",
    0x16: "Advent Commercial Fire 500",
    0x17: "Advent Commercial Fire 132",
    0x18: "Advent Commercial Burg 132",
}

# Concord zone types only
ZONE_TYPES = {
    0: 'Hardwired',
    1: 'RF',
    2: 'RF Touchpad',
}

# Concord zone types only
ZONE_TYPES = {
    0: 'Hardwired',
    1: 'RF',
    2: 'RF Touchpad',
}

NORMAL = 'Normal'
TRIPPED = 'Tripped'
FAULTED = 'Faulted'
ALARM   = 'Alarm'
TROUBLE = 'Trouble'
BYPASSED = 'Bypassed'

ZONE_STATES = {
    0: NORMAL,
    1: TRIPPED,
    2: FAULTED,
    4: ALARM,
    8: TROUBLE,
    10: BYPASSED,
}

# Concord arming levels
ARM_LEVEL = {
    1: 'Off',
    2: 'Stay',
    3: 'Away',
    8: 'Phone Test',
    9: 'Sensor Test',
}

def build_state_list(state_code, state_dict):
    states = 'Unknown'
    if state_code in state_dict:
        return state_dict[state_code];
    return states

def unwrap(val):
    if isinstance(val, dbus.ByteArray):
        return "".join([str(x) for x in val])
    if isinstance(val, (dbus.Array, list, tuple)):
        return [unwrap(x) for x in val]
    if isinstance(val, (dbus.Dictionary, dict)):
        return dict([(unwrap(x), unwrap(y)) for x, y in val.items()])
    if isinstance(val, (dbus.Signature, dbus.String)):
        return str(val)
    if isinstance(val, dbus.Boolean):
        return bool(val)
    if isinstance(val, (dbus.Int16, dbus.UInt16, dbus.Int32, dbus.UInt32, dbus.Int64, dbus.UInt64)):
        return int(val)
    if isinstance(val, dbus.Byte):
        return bytes([int(val)])
    return val 

class AlarmPanelInterface(object):
    def __init__(self, logger, configfile):
        self.logger = logger
        self.logger.debug("Starting")

        self._configfile = configfile
        self._zones_config = {}
        self._load_config()
     
        self.display_messages = [];

    def _load_config(self):
        self._config = configparser.ConfigParser()
        self._config.read(self._configfile)

        if self._config.has_section('zones'):
            for opt in self._config.options('zones'):
                number = opt
                name = self._config.get('zones', opt)
                self._zones_config[number] = name

    def _write_config(self):
        if not self._config.has_section('zones'):
            self._config.add_section('zones')

        for key,value in self._zones_config.items():
            if (not self._config.has_option('zones', key) and
                    value != 'Unknown'):
                self._config.set('zones', key, value)
        try:
            with open(self._configfile, 'w') as configfile:
                self._config.write(configfile)
        except IOError as ex:
            LOG.error('Unable to write %s: %s' % (self._configfile, ex))


    def get_panel(self):
        self.logger.debug("start get_panel") 
        panel = {}
 
        system_bus = dbus.SystemBus()
        proxy = system_bus.get_object('net.voria.concordd',
                                      '/net/voria/concordd')
        props = unwrap(proxy.get_info(dbus_interface='net.voria.concordd.v1'))

        panel['panel_type'] = PANEL_TYPES[props['panelType']]
        panel['hardware_revision'] = props['hwRevision']
        panel['software_revision'] = props['swRevision']
        panel['serial_number'] = props['serialNumber']
 
        return panel

    def get_zones(self):
        self.logger.debug("start get_zones")
        zones = {}

        system_bus = dbus.SystemBus()

        for i in range(96):
            try: 
                proxy = system_bus.get_object('net.voria.concordd',
                                              f"/net/voria/concordd/zone/{i}")
                info = unwrap(proxy.get_info(dbus_interface='net.voria.concordd.v1'))

                zone = { 
                    'partition_number': info['partitionId'],
                    'area_number': 0,
                    'group_number': info['group'],
                    'zone_number': info['zoneId'],
                    'zone_type': ZONE_TYPES.get(info['type'], 'Unknown'),
                    'zone_state': build_state_list(info['isTripped'], ZONE_STATES),
                    'zone_text': '',
                    'zone_text_tokens': [ ],
                }
                identifier = 'p' + str(zone['partition_number']) + 'z' + str(zone['zone_number'])

                if (zone['zone_text'] == ""): 
                    if identifier in self._zones_config:
                        zone['zone_text'] = self._zones_config[identifier]
                    else:
                        self._zones_config[identifier] = zone['zone_text']
                        self._write_config()

                zones[identifier] = zone
            except dbus.exceptions.DBusException as ex: 
                self.logger.debug(f"zone '{i}' not found")

        return zones

    def get_partitions(self):
        self.logger.debug("start get_partitions")
        partitions = {}

        system_bus = dbus.SystemBus()
        proxy = system_bus.get_object('net.voria.concordd',
                                      '/net/voria/concordd')
        partition_paths = unwrap(proxy.get_partitions(dbus_interface='net.voria.concordd.v1'))
        for partition_path in partition_paths: 
            partition_id = int(partition_path.replace('/net/voria/concordd/partition/', ''))
            partition_proxy = system_bus.get_object('net.voria.concordd',
                                                    partition_path)
            info = unwrap(partition_proxy.get_info(dbus_interface='net.voria.concordd.v1'))
            partition = { 
                'partition_number': partition_id,
                'area_number': 0,
                'arming_level': ARM_LEVEL.get(info['armLevel'], 'Unknown Arming Level'),
                'arming_level_code': info['armLevelUser'],
                'partition_text': '',
            } 
            partitions[partition['partition_number']] = partition
 
        return partitions

    def refresh(self):
        self.logger.debug("start refresh") 
        system_bus = dbus.SystemBus()
        proxy = system_bus.get_object('net.voria.concordd',
                                      '/net/voria/concordd')
        proxy.refresh(dbus_interface='net.voria.concordd.v1')


    def send_keypress(self, keys, partition=1, no_check=False):
        self.logger.debug("start send_keypress")
        
    def arm_stay(self,option):
        if option == None:
          self.logger.debug("start arm_stay")
        elif option == 'silent':
            self.logger.debug("start arm_stay silent")
        elif option == 'instant':
            self.logger.debug("start arm_stay instant")

    def arm_away(self,option):
        if option == None:
            self.logger.debug("start arm_away")
        elif option == 'silent':
            self.logger.debug("start arm_away silent")
        elif option == 'instant':
            self.logger.debug("start arm_away instant")

    def send_keys(self, keys, group):
        msg = []
        for k in keys:
            a = list(KEYPRESS_CODES.keys())[list(KEYPRESS_CODES.values()).index(str(k))]
            if group:               
                msg.append(a)
            else:
                self.logger.info("Sending key: %r" % msg)
                #self.send_keypress([a])        

        if group:
            self.logger.info("Sending group of keys: %r" % msg)
            #self.send_keypress(msg)    
       

    def disarm(self,master_pin):
        self.master_pin = master_pin
        #self.send_keypress([0x20])
        
       
 
