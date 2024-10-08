from enum import Enum

import copy
import os
import re
import yaml


class Mapper:
    def __init__(self):
        # Lazy load item_db until required
        self.item_db = None

        self.schema = {
            'Id': 'id',
            'AegisName': 'dbname',
            'Name': 'name',
            # 'JapaneseName': None, # not provided by DP
            'Level': lambda d: d['stats'].get('level', 0) if d.get('stats') else 0,
            'Hp': lambda d: d['stats'].get('health', 0) if d.get('stats') else 0,
            'Sp': self._sp,
            'BaseExp': lambda d: d['stats'].get('baseExperience', 0) if d.get('stats') else 0,
            'JobExp': lambda d: d['stats'].get('jobExperience', 0) if d.get('stats') else 0,
            # 'MvpExp': None, # not provided by 'DP'
            'Attack': lambda d: d['stats'].get('atk1', 0) if d.get('stats') else 0,
            'Attack2': lambda d: d['stats'].get('atk2', 0) if d.get('stats') else 0,
            'Defense': lambda d: d['stats'].get('defense', 0) if d.get('stats') else 0,
            'MagicDefense': lambda d: d['stats'].get('magicDefense', 0) if d.get('stats') else 0,
            'Resistance': lambda d: d['stats'].get('res', 0) if d.get('stats') else 0,
            'MagicResistance': lambda d: d['stats'].get('mres', 0) if d.get('stats') else 0,
            'Str': lambda d: max(d['stats'].get('str', 1) if d['stats'].get('str') is not None else 0, 1),
            'Agi': lambda d: max(d['stats'].get('agi', 1) if d['stats'].get('agi') is not None else 0, 1),
            'Vit': lambda d: max(d['stats'].get('vit', 1) if d['stats'].get('vit') is not None else 0, 1),
            'Int': lambda d: max(d['stats'].get('int', 1) if d['stats'].get('int') is not None else 0, 1),
            'Dex': lambda d: max(d['stats'].get('dex', 1) if d['stats'].get('dex') is not None else 0, 1),
            'Luk': lambda d: max(d['stats'].get('luk', 1) if d['stats'].get('luk') is not None else 0, 1),
            'AttackRange': lambda d: d['stats'].get('attackRange', 0) if d.get('stats') else 0,
            'SkillRange': lambda d: d['stats'].get('aggroRange', 0) if d.get('stats') else 0,
            'ChaseRange': lambda d: d['stats'].get('escapeRange', 0) if d.get('stats') else 0,
            'Size': self._scale,
            'Race': self._race,
            'Element': self._element,
            'ElementLevel': self._elementLevel,
            'WalkSpeed': lambda d: min(int(d['stats'].get('movementSpeed', 0) or 200), 1000),
            'AttackDelay': lambda d: max(int(d['stats'].get('rechargeTime', 0) or 0), 1),
            'AttackMotion': lambda d: max(int(d['stats'].get('attackSpeed', 0) or 0), 1),
            'DamageMotion': lambda d: max(int(d['stats'].get('attackedSpeed', 0) or 0), 1),
            'DamageTaken': self._damageTaken,
            'Ai': self._ai,
            'Class': self._class,
            'Modes': self._modes,
            'MvpDrops': self._mvpdrops,
            'Drops': self._drops,
        }


        self.drops_schema = {
            'Item': lambda d: self.item_db[d['itemId']] if d['itemId'] in self.item_db else d['itemId'],
            'Rate': 'chance',
            'StealProtected': lambda d: True if d['stealProtected'] else None,
            'RandomOptionGroup': lambda d: d['optionGroup'] if 'optionGroup' in d and d['optionGroup'] != 'G0' else None
            # 'Index': None, # not provided by DP
        }

        self.element_map = {
            0: 'Neutral',
            1: 'Water',
            2: 'Earth',
            3: 'Fire',
            4: 'Wind',
            5: 'Poison',
            6: 'Holy',
            7: 'Dark',
            8: 'Ghost',
            9: 'Undead',
        }

        self.scale_map = {
            0: 'Small',
            1: 'Medium',
            2: 'Large',
        }

        self.race_map = {
            0: 'Formless',
            1: 'Undead',
            2: 'Brute',
            3: 'Plant',
            4: 'Insect',
            5: 'Fish',
            6: 'Demon',
            7: 'Demihuman',
            8: 'Angel',
            9: 'Dragon',
        }

        self.class_map = {
            0: None, # 'Normal' is default and omitted
            1: 'Boss',
            2: 'Guardian',
            4: 'Battlefield',
            5: 'Event',
            6: 'Champion',
        }

    # Used for lazy loading item_db.yml as loading is slow
    def _require_item_db(self):
        if self.item_db is None:
            current_path = os.path.join(os.getcwd(), os.path.dirname(__file__))
            item_db_path = os.path.join(os.path.realpath(current_path), 'db', 'item_db.yml')
            self.item_db = yaml.load(open(item_db_path, encoding='utf-8'), Loader=yaml.FullLoader)['items']

    def _validate(self, data, *argv):
        for arg in argv:
            assert arg in data
            v = data[arg]
            msg = f'Unrecognised {arg}: {v}'
            if arg == 'scale':
                assert v in [None, 0, 1, 2], msg
            elif arg == 'element':
                assert v is None or v == 0 or (v >= 20 and v <= 89), msg
            elif arg == 'mvp':
                assert v in [0, 1], msg
            elif arg == 'ai':
                assert v == "" or v.startswith('MONSTER_TYPE_'), msg
            elif arg == 'class':
                assert v in [0, 1, 2, 4, 5, 6], msg

    def _sp(self, data):
        self._validate(data['stats'], 'sp')
        sp = data['stats']['sp']
        if sp is None or sp == 1 or sp < 0:
            return None
        return sp

    def _scale(self, data):
        self._validate(data['stats'], 'scale')
        scale = data['stats']['scale']
        if scale is None:
            return 'Small'
        return self.scale_map[scale]

    def _race(self, data):
        self._validate(data['stats'], 'race')
        race = data['stats']['race']
        if race is None or race < 0 or race > 9:
            return 'Formless'
        return self.race_map[race]

    def _element(self, data):
        self._validate(data['stats'], 'element')
        element = data['stats']['element']
        if element is None:
            return 'Neutral'
        return self.element_map[element % 10]

    def _elementLevel(self, data):
        self._validate(data['stats'], 'element')
        element = data['stats']['element']
        if element is None:
            return '1'
        return int(element / 20)

    # 10% for MVPs, 100% for all other mobs
    def _damageTaken(self, data):
        self._validate(data['stats'], 'attr')
        if data['stats']['attr'] & 0x200:
            return 10
        elif data['stats']['attr'] & 0x400:
            return 1
        else:
            return None

    # Define the _modes method
    def _modes(self, data):
        modes = {}
        if 'mvpdrops' in data and data['mvpdrops']:
            modes['Mvp'] = True

        race = data['stats'].get('race')
        if race in [4, 6]:  # Assuming '4' is Insect and '6' is Demon
            modes['Detector'] = True

        # Check if the monster is a Boss
        monster_class = data['stats'].get('class')
        if monster_class == 1:  # Assuming '1' represents Boss class
            modes.pop('Detector', None)

        # Check the attr value and set the corresponding modes
        attr = data['stats'].get('attr')
        if attr is not None:
            if attr & 1:
                modes['Ignoremelee'] = True
            if attr & 2:
                modes['Ignoremagic'] = True
            if attr & 4:
                modes['Ignoreranged'] = True
            if attr & 16:
                modes['Ignoremisc'] = True
            if attr & 32:
                modes['Knockbackimmune'] = True

        if modes:
            return modes
        return None

    # Last two characters e.g. 'MONSTER_TYPE_13' -> 13
    def _ai(self, data):
        self._validate(data['stats'], 'ai')
        if data['stats']['ai'] == '':
            return None
        return data['stats']['ai'][-2:]

    def _class(self, data):
        self._validate(data['stats'], 'class')
        return self.class_map[data['stats']['class']]

    def _mvpdrops(self, data):
        return self._drops(data, 'mvpdrops')

    def _drops(self, data, field='drops'):
        self._require_item_db()
        self._validate(data, field)
        result = list()
        for item in data[field]:
            if item['chance'] > 0:
                result.append(self._map_schema(copy.copy(self.drops_schema), item))
        if len(result) == 0:
            return None
        return result

    def _map_schema(self, schema, data):
        if schema is None:
            return None
        elif data is None:
            return schema
        result = copy.deepcopy(schema)
        for k, v in schema.items():
            if v is None:
                del result[k]
            elif callable(v):
                if v(data) == None:
                    del result[k]
                else:
                    result[k] = v(data)
            elif type(v) is dict:
                result[k] = self._map_schema(v, data)
            elif type(v) is str or type(v) is int:
                if v not in data or data[v] == 0 or data[v] == None:
                    del result[k]
                else:
                    result[k] = data[v]
            else:
                result[k] = v
        return result

    def map_mob(self, data):
        if data is None or 'Error' in data:
            return data
        elif 'stats' not in data or len(data['stats']) == 0:
            return {'Id': data['id'], 'AegisName': data['dbname'], 'Error': 'Mob stat data missing'}
        elif 'name' not in data or data['name'] is None:
            data['name'] = data['dbname']  # Assign 'dbname' to 'name' if 'name' is missing or None
        return self._map_schema(self.schema, data)
