# Copyright (c) 2015-2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2026 Alberto Gacías <alberto@migasfree.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import logging

from celery import shared_task

from ..client.models import Computer
from .models import Capability, Configuration, LogicalName, Node

logger = logging.getLogger('celery')

MAXINT = 9223372036854775807  # sys.maxint = (2**63) - 1


def _normalize_size(size):
    """Normalize size to a valid BigInteger value or 0."""
    try:
        size = int(size)
    except (TypeError, ValueError):
        return 0
    return size if (MAXINT >= size >= -MAXINT - 1) else 0


def _collect_hardware_nodes(computer, node_data, parent_id=None, level=1, nodes=None, related_data=None):
    """
    Recursively collects hardware node data and related objects into lists.

    Args:
        computer: Computer instance
        node_data: Dict with hardware node data from lshw
        parent_id: Temporary parent index (position in nodes list) or None for root
        level: Current hierarchy level
        nodes: List to collect Node instances
        related_data: List to collect (node_index, type, data) tuples

    Returns:
        Tuple of (nodes_list, related_data_list)
    """
    if nodes is None:
        nodes = []
    if related_data is None:
        related_data = []

    current_index = len(nodes)

    node = Node(
        parent_id=None,  # Will be set after bulk_create
        computer=computer,
        level=level,
        name=str(node_data.get('id', '')),
        class_name=node_data.get('class', ''),
        enabled=node_data.get('enabled', False),
        claimed=node_data.get('claimed', False),
        description=node_data.get('description'),
        vendor=node_data.get('vendor'),
        product=node_data.get('product'),
        version=node_data.get('version'),
        serial=node_data.get('serial'),
        bus_info=node_data.get('businfo'),
        physid=node_data.get('physid'),
        slot=node_data.get('slot'),
        size=_normalize_size(node_data.get('size', 0)),
        capacity=node_data.get('capacity'),
        clock=node_data.get('clock'),
        width=node_data.get('width'),
        dev=node_data.get('dev'),
    )
    # Store parent_index temporarily for later resolution
    node._temp_parent_index = parent_id
    nodes.append(node)

    # Collect related data
    for key in node_data:
        if key == 'children':
            for child in node_data[key]:
                _collect_hardware_nodes(computer, child, current_index, level + 1, nodes, related_data)
        elif key == 'capabilities':
            for name, description in node_data[key].items():
                related_data.append((current_index, 'capability', {'name': name, 'description': description}))
        elif key == 'configuration':
            for name, value in node_data[key].items():
                related_data.append((current_index, 'configuration', {'name': name, 'value': value}))
        elif key == 'logicalname':
            if isinstance(node_data[key], str):
                related_data.append((current_index, 'logicalname', {'name': node_data[key]}))
            else:
                for name in node_data[key]:
                    related_data.append((current_index, 'logicalname', {'name': name}))

    return nodes, related_data


@shared_task(queue='default')
def save_computer_hardware(computer_id, node_data, parent=None, level=1):
    """
    Save hardware data for a computer using bulk operations.

    This optimized version collects all hardware nodes and their related objects
    (capabilities, configurations, logical names) in memory, then uses bulk_create
    to insert them in batches, significantly reducing database round-trips.

    Args:
        computer_id: ID of the computer to save hardware for
        node_data: Hardware data dictionary from lshw
        parent: Deprecated, kept for backward compatibility
        level: Deprecated, kept for backward compatibility
    """
    computer = Computer.objects.get(id=computer_id)

    # Phase 1: Collect all nodes and related data in memory
    nodes, related_data = _collect_hardware_nodes(computer, node_data)

    if not nodes:
        computer.update_hardware_resume()
        computer.update_last_hardware_capture()
        return

    # Phase 2: Bulk create nodes in levels to resolve parent references
    # Group nodes by level to ensure parents are created before children
    levels = {}
    for idx, node in enumerate(nodes):
        levels.setdefault(node.level, []).append((idx, node))

    # Map from temporary index to actual DB object
    index_to_node = {}

    for level_num in sorted(levels.keys()):
        level_nodes = levels[level_num]

        # Set parent_id from previously created nodes
        for _, node in level_nodes:
            parent_index = node._temp_parent_index
            if parent_index is not None and parent_index in index_to_node:
                node.parent = index_to_node[parent_index]
            delattr(node, '_temp_parent_index')

        # Bulk create this level's nodes
        nodes_to_create = [node for _, node in level_nodes]
        created_nodes = Node.objects.bulk_create(nodes_to_create)

        # Map indices to created nodes
        for (idx, _), created_node in zip(level_nodes, created_nodes, strict=False):
            index_to_node[idx] = created_node

    # Phase 3: Bulk create related objects
    capabilities = []
    configurations = []
    logical_names = []

    for node_index, obj_type, data in related_data:
        node = index_to_node.get(node_index)
        if node is None:
            continue

        if obj_type == 'capability':
            capabilities.append(Capability(node=node, name=data['name'], description=data.get('description')))
        elif obj_type == 'configuration':
            configurations.append(Configuration(node=node, name=data['name'], value=data.get('value')))
        elif obj_type == 'logicalname':
            logical_names.append(LogicalName(node=node, name=data['name']))

    if capabilities:
        Capability.objects.bulk_create(capabilities, ignore_conflicts=True)
    if configurations:
        Configuration.objects.bulk_create(configurations, ignore_conflicts=True)
    if logical_names:
        LogicalName.objects.bulk_create(logical_names, ignore_conflicts=True)

    computer.update_hardware_resume()
    computer.update_last_hardware_capture()
