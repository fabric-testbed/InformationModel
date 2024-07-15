"""
A collection of simple methods for consistently creating identifiers for things

Author: Ilya Baldin (ibaldin@renci.org), Xi Yang (xiyang@es.net)
"""
from typing import Tuple


def mac_to_node_id(mac: str) -> str:
    """
    turn mac address into a unique string to act
    as node id, but don't make it look like mac address
    :param mac:
    :return:
    """

    return 'node_id-' + mac.replace(':', '-')


def dp_switch_name_id(site: str, ip: str) -> Tuple[str, str]:
    """
    Return a tuple of name and id of a switch name and node id
    :param site:
    :param ip:
    :return:
    """
    name = site.lower() + '-data-sw'
    return name,  'node+' + name + ':ip+' + ip


def dp_port_id(switch: str, port: str) -> str:
    """
    Return a unique id of a DP switch port based on switch name and port name
    :param switch:
    :param port:
    :return:
    """
    return 'port+' + switch + ':' + port


def p4_switch_name_id(site: str, ip: str) -> Tuple[str, str]:
    """
    Return a tuple of name and id of a p4 switch name and node id
    :param site:
    :param ip:
    :return:
    """
    name = site.lower() + '-p4-sw'
    return name,  'node+' + name + ':ip+' + ip
