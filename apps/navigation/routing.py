"""
apps/navigation/routing.py

MarketGraph — builds an in-memory graph from a Market's Nodes and Edges,
then runs A* (with Euclidean heuristic) to find the shortest path between
any two nodes. Falls back to Dijkstra when no heuristic can be applied.

Usage:
    graph = MarketGraph(market)
    result = graph.route(from_node_id, to_node_id)
    # result = {
    #   "path": [node_id, ...],
    #   "distance": 42.5,
    #   "steps": ["Walk straight 8m to Junction B3", "Turn right into Zone C", ...],
    # }
"""

import math
import heapq
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from apps.markets.models import Market, Node, Edge


# ---------------------------------------------------------------------------
# Graph data structures
# ---------------------------------------------------------------------------

@dataclass
class GraphNode:
    id: int
    label: str
    x: float
    y: float
    zone_name: str = ""
    node_type: str = "stall"


@dataclass(order=True)
class _PQEntry:
    """Priority queue entry for A*."""
    priority: float
    node_id: int = field(compare=False)


# ---------------------------------------------------------------------------
# MarketGraph
# ---------------------------------------------------------------------------

class MarketGraph:
    """
    In-memory graph for a single Market.

    Build once per request (or cache invalidated on Market/Node/Edge change).
    Thread-safe for reads; not designed for concurrent writes.
    """

    def __init__(self, market: Market):
        self.market = market
        self._nodes: Dict[int, GraphNode] = {}
        self._adjacency: Dict[int, List[Tuple[int, float]]] = {}  # node_id → [(neighbour_id, weight)]
        self._build()

    def _build(self):
        """Load nodes and edges from the database into memory."""
        nodes_qs = Node.objects.filter(market=self.market, is_active=True).select_related("zone")
        for n in nodes_qs:
            self._nodes[n.id] = GraphNode(
                id=n.id,
                label=n.label,
                x=n.x,
                y=n.y,
                zone_name=n.zone.name if n.zone else "",
                node_type=n.node_type,
            )
            self._adjacency[n.id] = []

        edges_qs = Edge.objects.filter(market=self.market, is_active=True)
        for e in edges_qs:
            if e.node_from_id in self._adjacency and e.node_to_id in self._nodes:
                self._adjacency[e.node_from_id].append((e.node_to_id, e.weight))
                # Undirected: add reverse
                if e.node_to_id in self._adjacency:
                    self._adjacency[e.node_to_id].append((e.node_from_id, e.weight))

    # ------------------------------------------------------------------
    # Heuristic
    # ------------------------------------------------------------------

    def _heuristic(self, a_id: int, b_id: int) -> float:
        """Euclidean distance between two graph nodes (map coordinate units)."""
        a = self._nodes[a_id]
        b = self._nodes[b_id]
        return math.hypot(a.x - b.x, a.y - b.y)

    # ------------------------------------------------------------------
    # A* pathfinding
    # ------------------------------------------------------------------

    def _astar(self, start_id: int, goal_id: int) -> Optional[Tuple[List[int], float]]:
        """
        Returns (path_as_list_of_node_ids, total_distance) or None if no path exists.
        """
        open_heap: List[_PQEntry] = []
        heapq.heappush(open_heap, _PQEntry(0.0, start_id))

        g_score: Dict[int, float] = {start_id: 0.0}
        came_from: Dict[int, Optional[int]] = {start_id: None}

        while open_heap:
            current = heapq.heappop(open_heap).node_id

            if current == goal_id:
                return self._reconstruct_path(came_from, goal_id), g_score[goal_id]

            for neighbour_id, weight in self._adjacency.get(current, []):
                tentative_g = g_score[current] + weight
                if tentative_g < g_score.get(neighbour_id, math.inf):
                    came_from[neighbour_id] = current
                    g_score[neighbour_id] = tentative_g
                    f = tentative_g + self._heuristic(neighbour_id, goal_id)
                    heapq.heappush(open_heap, _PQEntry(f, neighbour_id))

        return None  # No path found

    def _reconstruct_path(self, came_from: Dict[int, Optional[int]], goal_id: int) -> List[int]:
        path = []
        current: Optional[int] = goal_id
        while current is not None:
            path.append(current)
            current = came_from[current]
        path.reverse()
        return path

    # ------------------------------------------------------------------
    # Direction generation
    # ------------------------------------------------------------------

    def _bearing(self, from_node: GraphNode, to_node: GraphNode) -> float:
        """Returns the compass bearing in degrees (0=North/up, 90=East/right)."""
        dx = to_node.x - from_node.x
        dy = to_node.y - from_node.y  # positive = downward on most map coords
        angle = math.degrees(math.atan2(dx, -dy))
        return angle % 360

    def _bearing_to_direction(self, bearing: float) -> str:
        directions = [
            (22.5, "north"),
            (67.5, "northeast"),
            (112.5, "east"),
            (157.5, "southeast"),
            (202.5, "south"),
            (247.5, "southwest"),
            (292.5, "west"),
            (337.5, "northwest"),
        ]
        for threshold, label in directions:
            if bearing < threshold:
                return label
        return "north"

    def _turn_instruction(self, prev_bearing: Optional[float], curr_bearing: float) -> str:
        """Converts a change in bearing into a turn instruction."""
        if prev_bearing is None:
            return "Head"
        diff = (curr_bearing - prev_bearing + 360) % 360
        if diff < 30 or diff > 330:
            return "Continue straight"
        elif diff < 80:
            return "Turn slightly right"
        elif diff < 170:
            return "Turn right"
        elif diff < 190:
            return "Turn around"
        elif diff < 280:
            return "Turn left"
        else:
            return "Turn slightly left"

    def _build_steps(self, path: List[int]) -> List[str]:
        """Converts a list of node IDs into human-readable direction steps."""
        if len(path) < 2:
            return ["You are already at your destination."]

        steps = []
        prev_bearing: Optional[float] = None

        for i in range(len(path) - 1):
            a = self._nodes[path[i]]
            b = self._nodes[path[i + 1]]
            distance = round(math.hypot(b.x - a.x, b.y - a.y))
            curr_bearing = self._bearing(a, b)
            cardinal = self._bearing_to_direction(curr_bearing)
            turn = self._turn_instruction(prev_bearing, curr_bearing)

            zone_note = f" into {b.zone_name}" if b.zone_name and b.zone_name != a.zone_name else ""
            is_last = (i == len(path) - 2)

            if is_last:
                step = f"{turn} {distance}m {cardinal}{zone_note} — arrive at {b.label}"
            else:
                step = f"{turn} {distance}m {cardinal}{zone_note} toward {b.label}"

            steps.append(step)
            prev_bearing = curr_bearing

        return steps

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def route(self, from_node_id: int, to_node_id: int) -> dict:
        """
        Find the shortest route between two nodes.

        Returns a dict with:
          - found (bool)
          - path ([node_id, ...])
          - distance (float, metres)
          - steps ([str, ...])
          - error (str, if not found)
        """
        if from_node_id not in self._nodes:
            return {"found": False, "error": f"Start node {from_node_id} not found in graph."}
        if to_node_id not in self._nodes:
            return {"found": False, "error": f"Destination node {to_node_id} not found in graph."}
        if from_node_id == to_node_id:
            return {
                "found": True, "path": [from_node_id],
                "distance": 0, "steps": ["You are already at your destination."],
            }

        result = self._astar(from_node_id, to_node_id)
        if result is None:
            return {"found": False, "error": "No walkable path exists between these two locations."}

        path, total_distance = result
        steps = self._build_steps(path)
        node_labels = [self._nodes[nid].label for nid in path]

        return {
            "found": True,
            "path": path,
            "node_labels": node_labels,
            "distance": round(total_distance, 1),
            "steps": steps,
        }

    def search_vendors(self, query: str) -> List[GraphNode]:
        """
        Simple node-level search by label (delegates to DB for vendor/product search).
        Returns matching GraphNodes.
        """
        q = query.lower()
        return [n for n in self._nodes.values() if q in n.label.lower()]
