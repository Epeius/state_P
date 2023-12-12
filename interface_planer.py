# -*- coding: utf-8 -*-
from actors.actors import *
import pickle
import argparse
import json
import base64
from program_state.state import revertStateChainFromNetwork

SUPPORTED_ACTIONS = [
    "state_construct_empty_states_P",
    "state_append_concrete_ip_constraint_P",
    "state_append_concrete_sp_constraint_P",
    "state_append_concrete_sp_mem_constraint_P",
    "state_append_concrete_reg_constraint_P",
    "state_append_concrete_mem_constraint_P",
    "state_append_concrete_reg_mem_constraint_P",
    "state_merge_concrete_sp_constraint_P",
    "state_merge_concrete_sp_mem_constraint_P",
    "state_merge_concrete_reg_constraint_P",
    "state_merge_concrete_mem_constraint_P",
    "state_merge_concrete_reg_mem_constraint_P",
    "state_append_controllable_ip_constraint_P",
    "state_append_controllable_sp_constraint_P",
    "state_append_controllable_sp_mem_constraint_P",
    "state_append_controllable_reg_constraint_P",
    "state_append_controllable_mem_constraint_P",
    "state_append_controllable_reg_mem_constraint_P",
    "state_merge_controllable_sp_mem_constraint_P",
    "state_merge_controllable_reg_constraint_P",
    "state_merge_controllable_mem_constraint_P",
    "state_merge_controllable_reg_mem_constraint_P"
]


class StateModifier:
    def __init__(self, action_name, session_id, old_states, arguments):
        self._action_name = action_name
        self._session_id = session_id
        self._old_states = old_states
        self._arguments = arguments

    def get_new_states(self):
        new_states = eval(self._action_name)(self._old_states, self._arguments[1:-1])
        return new_states


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="输入的谓词信息，json格式")
    parser.add_argument("-f", "--file", help="采用文件的形式输入谓词数据，json格式")

    args = parser.parse_args()

    if args.input:
        input_json = json.loads(args.input)
        session_id = input_json['session_id']
        query_info = input_json['query']
        action_name = query_info['query_name']
        args = query_info['args']

        if action_name not in SUPPORTED_ACTIONS:
            print(json.dumps( {
                'processed': 0,
                'res': {"status": 0, "info": "ERROR", "data": {"Invalid query_name!"}}
            }))
            return

        if 'index' in input_json:
            if input_json['index'] > 0:
                print(json.dumps({
                    'processed': 0,
                    'res': {"status": 1, "info": "ok", "data": {"valid": 0, "args": []}}
                }))
                return
            else:
                if action_name != "state_construct_empty_states_P":
                    serialized_old_states_b64 = args[0]['value']
                    serialized_old_states = bytes(base64.b64decode(serialized_old_states_b64))
                    old_states = pickle.loads(serialized_old_states)
                else:
                    old_states = None

                SM = StateModifier(action_name=action_name, session_id=session_id, old_states=old_states, arguments=args)
                new_states = SM.get_new_states()

                serialized_new_states = pickle.dumps(new_states)
                serialized_new_states_b64 = str(base64.b64encode(serialized_new_states), encoding='utf-8')
                args = args[:-1]
                args.append({'type': 'str', 'value': str(serialized_new_states_b64), 'concrete': 1})

        print(json.dumps({
            'processed': 1,
            'res':  {"status": 1, "info": "ok", "data": {"valid": 1, "args": args}}
        }))


if __name__ == "__main__":
    main()