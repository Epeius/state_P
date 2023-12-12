# -*- coding: utf-8 -*-
from program_state.state import *
from program_state.constraint import *
from program_state.expressions import *
from program_state.variables import *
import pickle


############### Utils Begin ############################
def construct_reg_eq_constraint(reg_name, concrete_value, comments=""):
    is_compose = not isinstance(concrete_value, int)
    reg_expr = VIRExpression(reg_name, is_unsigned=1, bit_width=64)
    if is_compose:
        target_expr = ConstExpression(concrete_value)
    else:
        lib_name = concrete_value['base']
        offset = concrete_value['offset']
        target_expr = OFBExpression(lib_name, ConstExpression(offset))
    eq_expr = EqExpression(reg_expr, target_expr)
    cons = Constraint(comments=comments)
    cons.add_expression(eq_expr)
    return cons


def construct_reg_controllable_constraint(reg_name, comments=""):
    ctrl_expr = REGCTLExpression(reg_name)
    cons = Constraint(comments=comments)
    cons.add_expression(ctrl_expr)
    return cons


def construct_reg_ptr_offset_constraint(reg_name, offset, value_list, comments=""):
    reg_value_expr = get_int_from_register(reg_name, is_unsigned=1, bit_width=64)
    index = 0
    cons = Constraint(comments=comments)
    for value in value_list:
        mem_value_expr = get_int_from_memory(AddExpression(reg_value_expr, ConstExpression(offset + index)),
                                             is_unsigned=1, bit_width=8)
        cons.add_expression(EqExpression(mem_value_expr, ConstExpression(value)))
        index += 1
    return cons


def construct_reg_ptr_offset_controllable_constraint(reg_name, offset, size, comments=""):
    reg_value_expr = get_int_from_register(reg_name, is_unsigned=1, bit_width=64)
    mem_start_expr = AddExpression(reg_value_expr, ConstExpression(offset))
    cons = Constraint(comments=comments)
    cons.add_expression(MEMCTLExpression(mem_start_expr, size_in_byte=size))
    return cons


def construct_mem_constraint(mem_address, value_list, comments=""):
    index = 0
    cons = Constraint(comments=comments)
    for value in value_list:
        mem_value_expr = get_int_from_memory(AddExpression(ConstExpression(mem_address), ConstExpression(index)),
                                             is_unsigned=1, bit_width=8)
        cons.add_expression(EqExpression(mem_value_expr, ConstExpression(value)))
        index += 1
    return cons


def construct_mem_controllable_constraint(mem_address, size, comments=""):
    mem_start_expr = ConstExpression(mem_address)
    cons = Constraint(comments=comments)
    cons.add_expression(MEMCTLExpression(mem_start_expr, size_in_byte=size))
    return cons

############### Utils End ############################


def state_construct_empty_states_P(old_states, args):
    """
    构建空的状态序列
    """
    states = StateChain()
    return states


def state_append_concrete_ip_constraint_P(old_states, args):
    """
    在旧的状态序列 OldStates 中增加⼀个状态，其中指令寄存器 IP 约束为指定的数值，
    需要注意的是 ConcreteValue 可能为⼀个具体的数值，也可能采⽤复合值例如 Base+Offset 的⽅式
    """
    concrete_value = args[0]['value']
    cons = construct_reg_eq_constraint('ip', concrete_value)
    new_state = State()
    new_state.add_constraint(cons)
    new_states = copy.deepcopy(old_states)
    new_states.append_state(new_state)
    return new_states


def state_append_concrete_sp_constraint_P(old_states, args):
    """
    在旧的状态序列 OldStates 中增加⼀个状态，其中栈顶寄存器 SP 约束为指定的数值，
    需要注意的是 ConcreteValue 可能为⼀个具体的数值，也可能采⽤复合值例如 Base+Offset 的⽅式
    """
    concrete_value = args[0]['value']
    cons = construct_reg_eq_constraint('sp', concrete_value)
    new_state = State()
    new_state.add_constraint(cons)
    new_states = copy.deepcopy(old_states)
    new_states.append_state(new_state)
    return new_states


def state_append_concrete_sp_mem_constraint_P(old_states, args):
    """
    在旧的状态序列 OldStates 中增加⼀个状态，其中栈顶寄存器 SP +Offset 指向的内存约束为指定的数值，
    需要注意的是 ConcreteData 为整数列表形式，如 [31,32,44,35, 32]
    """
    offset = args[0]['value']
    concrete_data = args[1]['value']
    cons = construct_reg_ptr_offset_constraint('sp', offset, concrete_data)
    new_state = State()
    new_state.add_constraint(cons)
    new_states = copy.deepcopy(old_states)
    new_states.append_state(new_state)
    return new_states


def state_append_concrete_reg_constraint_P(old_states, args):
    """
    在旧的状态序列 OldStates 中增加⼀个状态，其中寄存器 RegName 约束为指定的数值，
    需要注意的是 ConcreteValue 可能为⼀个具体的数值，也可能采⽤复合值例如 Base+Offset 的⽅式
    """
    reg_name = args[0]['value']
    concrete_value = args[1]['value']
    cons = construct_reg_eq_constraint(reg_name, concrete_value)
    new_state = State()
    new_state.add_constraint(cons)
    new_states = copy.deepcopy(old_states)
    new_states.append_state(new_state)
    return new_states


def state_append_concrete_mem_constraint_P(old_states, args):
    """
    在旧的状态序列 OldStates 中增加⼀个状态，其中内存地址 MemAddress 指向的内存约束为指定的数值（整数列表形式），
    """
    mem_address = args[0]['value']
    concrete_data = args[1]['value']
    cons = construct_mem_constraint(mem_address, concrete_data)
    new_state = State()
    new_state.add_constraint(cons)
    new_states = copy.deepcopy(old_states)
    new_states.append_state(new_state)
    return new_states


def state_append_concrete_reg_mem_constraint_P(old_states, args):
    """
    在旧的状态序列 OldStates 中增加⼀个状态，其中寄存器 RegName +Offset 指向的内存约束为指定的数值，
    需要注意的是 ConcreteData 为整数列表形式，如 [31,32,44,35, 32]
    """
    reg_name = args[0]['value']
    offset = args[1]['value']
    concrete_data = args[2]['value']
    cons = construct_reg_ptr_offset_constraint(reg_name, offset, concrete_data)
    new_state = State()
    new_state.add_constraint(cons)
    new_states = copy.deepcopy(old_states)
    new_states.append_state(new_state)
    return new_states


def state_merge_concrete_sp_constraint_P(old_states, args):
    """
    在旧的状态序列 OldStates 的最后⼀个状态融合⼀个新的 SP 具体值约束
    （融合表⽰如果 OldStates 为空，则添加⼀个状态；
    如果最后⼀个状态中已经有 SP 的约束，则更新约束；如果最后⼀个状态中没有针对 SP 的约束，则增加约束）
    """
    concrete_value = args[0]['value']
    cons = construct_reg_eq_constraint('sp', concrete_value)
    if old_states.num_states != 0:
        new_states = copy.deepcopy(old_states)
        last_state = new_states.get_state_by_index(new_states.num_states - 1)
        last_state.add_constraint(cons)
    else:
        new_state = State()
        new_state.add_constraint(cons)
        new_states = StateChain()
        new_states.append_state(new_state)
    return new_states


def state_merge_concrete_sp_mem_constraint_P(old_states, args):
    """
    在旧的状态序列 OldStates 的最后⼀个状态融合⼀个新的 SP 指向内存的约束， Offset 表⽰偏移； ConcreteData 为具
    体的约束数据
    """
    offset = args[0]['value']
    concrete_data = args[1]['value']
    cons = construct_reg_ptr_offset_constraint('sp', offset, concrete_data)
    if old_states.num_states != 0:
        new_states = copy.deepcopy(old_states)
        last_state = new_states.get_state_by_index(new_states.num_states - 1)
        last_state.add_constraint(cons)
    else:
        new_state = State()
        new_state.add_constraint(cons)
        new_states = StateChain()
        new_states.append_state(new_state)
    return new_states


def state_merge_concrete_reg_constraint_P(old_states, args):
    """
    在旧的状态序列 OldStates 的最后⼀个状态融合⼀个新的寄存器约束（融合含义如上）
    ，其中 RegName 是寄存器名称， ConcreteValue 可能为⼀个具体的数值，也可能采⽤复合值例如 Base+Offset 的⽅式
    """
    reg_name = args[0]['value']
    concrete_value = args[1]['value']
    cons = construct_reg_eq_constraint(reg_name, concrete_value)
    if old_states.num_states != 0:
        new_states = copy.deepcopy(old_states)
        last_state = new_states.get_state_by_index(new_states.num_states - 1)
        last_state.add_constraint(cons)
    else:
        new_state = State()
        new_state.add_constraint(cons)
        new_states = StateChain()
        new_states.append_state(new_state)
    return new_states


def state_merge_concrete_mem_constraint_P(old_states, args):
    """
    在旧的状态序列 OldStates 的最后⼀个状态融合⼀个新的寄存器约束（融合含义如上）
    ，其中 MemAddress 是内存起始地址， ConcreteData 为具体的约束数值
    """
    mem_address = args[0]['value']
    concrete_data = args[1]['value']
    cons = construct_mem_constraint(mem_address, concrete_data)
    if old_states.num_states != 0:
        new_states = copy.deepcopy(old_states)
        last_state = new_states.get_state_by_index(new_states.num_states - 1)
        last_state.add_constraint(cons)
    else:
        new_state = State()
        new_state.add_constraint(cons)
        new_states = StateChain()
        new_states.append_state(new_state)
    return new_states


def state_merge_concrete_reg_mem_constraint_P(old_states, args):
    """
    在旧的状态序列 OldStates 的最后⼀个状态融合⼀个新的寄存器约束（融合含义如上）
    ，其中 RegName 是寄存器名称， Offset 是偏移， ConcreteData 为具体的约束数值
    """
    reg_name = args[0]['value']
    offset = args[1]['value']
    concrete_data = args[2]['value']
    cons = construct_reg_ptr_offset_constraint(reg_name, offset, concrete_data)
    if old_states.num_states != 0:
        new_states = copy.deepcopy(old_states)
        last_state = new_states.get_state_by_index(new_states.num_states - 1)
        last_state.add_constraint(cons)
    else:
        new_state = State()
        new_state.add_constraint(cons)
        new_states = StateChain()
        new_states.append_state(new_state)
    return new_states


def state_append_controllable_ip_constraint_P(old_states, args):
    """
    在旧的状态序列 OldStates 中增加一个状态，需要约束指令寄存器IP可控
    """
    cons = construct_reg_controllable_constraint('ip')
    new_state = State()
    new_state.add_constraint(cons)
    new_states = copy.deepcopy(old_states)
    new_states.append_state(new_state)
    return new_states


def state_append_controllable_sp_constraint_P(old_states, args):
    """
    在旧的状态序列 oldStates 中增加一个状态，需要约束栈顶寄存器 sP 可控
    """
    cons = construct_reg_controllable_constraint('sp')
    new_state = State()
    new_state.add_constraint(cons)
    new_states = copy.deepcopy(old_states)
    new_states.append_state(new_state)
    return new_states


def state_append_controllable_sp_mem_constraint_P(old_states, args):
    """
    在旧的状态序列 OldStates 中增加一个状态，需要约束栈顶寄存器 sp +offset 指向的内存可控,可控长度为 size
    """
    offset = args[0]['value']
    size = args[1]['value']
    cons = construct_reg_ptr_offset_controllable_constraint('sp', offset, size)
    new_state = State()
    new_state.add_constraint(cons)
    new_states = copy.deepcopy(old_states)
    new_states.append_state(new_state)
    return new_states


def state_append_controllable_reg_constraint_P(old_states, args):
    """
    在旧的状态序列 OldStates 中增加一个状态，需要约束寄存器 RegName 的值可控
    """
    reg_name = args[0]['value']
    cons = construct_reg_controllable_constraint(reg_name)
    new_state = State()
    new_state.add_constraint(cons)
    new_states = copy.deepcopy(old_states)
    new_states.append_state(new_state)
    return new_states


def state_append_controllable_mem_constraint_P(old_states, args):
    """
    在旧的状态序列 OldStates 中增加一个状态，需要内存 MemAddress 起始的内存 size 长度的数据的值可控
    """
    mem_addr = args[0]['value']
    size = args[1]['value']
    cons = construct_mem_controllable_constraint(mem_addr, size)
    new_state = State()
    new_state.add_constraint(cons)
    new_states = copy.deepcopy(old_states)
    new_states.append_state(new_state)
    return new_states


def state_append_controllable_reg_mem_constraint_P(old_states, args):
    """
    在旧的状态序列 OldStates 中增加一个状态，需要约束栈顶寄存器 reg_name +offset 指向的内存可控,可控长度为 size
    """
    reg_name = args[0]['value']
    offset = args[1]['value']
    size = args[2]['value']
    cons = construct_reg_ptr_offset_controllable_constraint(reg_name, offset, size)
    new_state = State()
    new_state.add_constraint(cons)
    new_states = copy.deepcopy(old_states)
    new_states.append_state(new_state)
    return new_states


def state_merge_controllable_sp_mem_constraint_P(old_states, args):
    offset = args[0]['value']
    size = args[1]['value']
    cons = construct_reg_ptr_offset_controllable_constraint('sp', offset, size)
    if old_states.num_states != 0:
        new_states = copy.deepcopy(old_states)
        last_state = new_states.get_state_by_index(new_states.num_states - 1)
        last_state.add_constraint(cons)
    else:
        new_state = State()
        new_state.add_constraint(cons)
        new_states = StateChain()
        new_states.append_state(new_state)
    return new_states


def state_merge_controllable_reg_constraint_P(old_states, args):
    reg_name = args[0]['value']
    cons = construct_reg_controllable_constraint(reg_name)
    if old_states.num_states != 0:
        new_states = copy.deepcopy(old_states)
        last_state = new_states.get_state_by_index(new_states.num_states - 1)
        last_state.add_constraint(cons)
    else:
        new_state = State()
        new_state.add_constraint(cons)
        new_states = StateChain()
        new_states.append_state(new_state)
    return new_states


def state_merge_controllable_mem_constraint_P(old_states, args):
    mem_addr = args[0]['value']
    size = args[1]['value']
    cons = construct_mem_controllable_constraint(mem_addr, size)
    if old_states.num_states != 0:
        new_states = copy.deepcopy(old_states)
        last_state = new_states.get_state_by_index(new_states.num_states - 1)
        last_state.add_constraint(cons)
    else:
        new_state = State()
        new_state.add_constraint(cons)
        new_states = StateChain()
        new_states.append_state(new_state)
    return new_states


def state_merge_controllable_reg_mem_constraint_P(old_states, args):
    reg_name = args[0]['value']
    offset = args[1]['value']
    size = args[2]['value']
    cons = construct_reg_ptr_offset_controllable_constraint(reg_name, offset, size)
    if old_states.num_states != 0:
        new_states = copy.deepcopy(old_states)
        last_state = new_states.get_state_by_index(new_states.num_states - 1)
        last_state.add_constraint(cons)
    else:
        new_state = State()
        new_state.add_constraint(cons)
        new_states = StateChain()
        new_states.append_state(new_state)
    return new_states
