import random
import itertools
from typing import List, Dict, Tuple, Any, Optional

class WFCSolver:
    def __init__(self, dimensions: List[int], domain: List[Any]):
        self.dimensions = dimensions
        self.domain = domain
        # Create a dict of coords to list of possible states
        self.grid: Dict[Tuple[int, ...], List[Any]] = {}
        self.weights: Dict[Tuple[int, ...], Dict[Any, float]] = {}
        
        # Generate all coordinates
        ranges = [range(d) for d in dimensions]
        for coord in itertools.product(*ranges):
            self.grid[coord] = list(domain)
            # Default weights = 1.0 for all states
            self.weights[coord] = {state: 1.0 for state in domain}
            
        self.constraints = []

    def add_constraint(self, constraint: Dict[str, Any]):
        """
        constraint format:
        {
            "type": "adjacency", 
            "state_1": val, 
            "state_2": val, 
            "offset": [1] or [1, 0] # relative offset where state_2 cannot be if state_1 is at current pos
        }
        or
        {
            "type": "state_weights",
            "condition": "index[0] % 2 != 0",
            "weights": {"0": 1.0, "1": 0.5, "default": 0.0}
        }
        """
        self.constraints.append(constraint)

    def _apply_initial_constraints(self):
        for coord in self.grid:
            # Evaluate positional constraints
            for c in self.constraints:
                if c["type"] == "state_weights":
                    if self._eval_condition(c.get("condition", "True"), coord):
                        weights_map = c.get("weights", {})
                        default_w = weights_map.get("default", 1.0)
                        
                        for state in self.grid[coord]:
                            str_state = str(state)
                            if str_state in weights_map:
                                w = float(weights_map[str_state])
                            else:
                                w = float(default_w)
                            self.weights[coord][state] *= w

    def _eval_condition(self, condition_str: str, index: Tuple[int, ...]) -> bool:
        try:
            return eval(condition_str, {}, {"index": index})
        except Exception:
            return False

    def _get_entropy(self, coord: Tuple[int, ...]) -> float:
        states = self.grid[coord]
        if len(states) <= 1:
            return float('inf') # Already collapsed or invalid
        
        # Simple entropy: number of available states, or we could use actual Shannon entropy based on weights.
        # For music, number of states is a fine heuristic, but let's add a small random tie-breaker
        return len(states) + random.random() * 0.1

    def _get_lowest_entropy_cell(self) -> Optional[Tuple[int, ...]]:
        min_e = float('inf')
        best_coord = None
        for coord, states in self.grid.items():
            if len(states) > 1:
                e = self._get_entropy(coord)
                if e < min_e:
                    min_e = e
                    best_coord = coord
        return best_coord

    def _collapse_cell(self, coord: Tuple[int, ...], adherence: float):
        states = self.grid[coord]
        if not states:
            raise ValueError(f"Contradiction at {coord}, no valid states left.")
        
        # Base weights from rules
        w_list = [self.weights[coord].get(s, 1.0) for s in states]
        
        # Linearly interpolate weights based on adherence
        if adherence <= 0.0:
            final_weights = [1.0 for _ in states]
        else:
            final_weights = [(w * adherence) + (1.0 * (1.0 - adherence)) for w in w_list]
            
        # Choose a state based on weights
        chosen_state = random.choices(states, weights=final_weights, k=1)[0]
        self.grid[coord] = [chosen_state]
        return chosen_state

    def _propagate(self, start_coord: Tuple[int, ...]):
        stack = [start_coord]
        
        while stack:
            curr_coord = stack.pop()
            curr_states = self.grid[curr_coord]
            
            # For each adjacency constraint, check neighbors
            for c in self.constraints:
                if c["type"] == "adjacency":
                    offset = tuple(c["offset"])
                    neighbor_coord = tuple(curr_coord[i] + offset[i] for i in range(len(curr_coord)))
                    
                    if neighbor_coord in self.grid:
                        # If curr is definitively state_1, then neighbor cannot be state_2
                        state_1 = c["state_1"]
                        state_2 = c["state_2"]
                        
                        if len(curr_states) == 1 and curr_states[0] == state_1:
                            if state_2 in self.grid[neighbor_coord]:
                                self.grid[neighbor_coord].remove(state_2)
                                stack.append(neighbor_coord)
                                
                        # Reverse propagation: if neighbor is definitely state_2, curr cannot be state_1
                        reverse_offset = tuple(-x for x in offset)
                        rev_neighbor_coord = tuple(curr_coord[i] + reverse_offset[i] for i in range(len(curr_coord)))
                        if rev_neighbor_coord in self.grid:
                            if len(curr_states) == 1 and curr_states[0] == state_2:
                                if state_1 in self.grid[rev_neighbor_coord]:
                                    self.grid[rev_neighbor_coord].remove(state_1)
                                    stack.append(rev_neighbor_coord)

    def solve(self, max_attempts=10, adherence=1.0) -> Optional[Dict[Tuple[int, ...], Any]]:
        for attempt in range(max_attempts):
            try:
                # Reset
                ranges = [range(d) for d in self.dimensions]
                for coord in itertools.product(*ranges):
                    self.grid[coord] = list(self.domain)
                    self.weights[coord] = {state: 1.0 for state in self.domain}
                    
                self._apply_initial_constraints()
                
                while True:
                    # Find lowest entropy
                    coord = self._get_lowest_entropy_cell()
                    if coord is None:
                        break # All collapsed
                        
                    self._collapse_cell(coord, adherence)
                    self._propagate(coord)
                    
                # Return final grid
                return {k: v[0] for k, v in self.grid.items()}
            except ValueError:
                # Backtrack / retry
                continue
                
        return None # Failed to find a solution

    def to_nested_list(self, result_dict: Dict[Tuple[int, ...], Any]) -> List[Any]:
        # For 1D, returns a list. For 2D, a list of lists.
        def _build(dim_idx, current_prefix):
            if dim_idx == len(self.dimensions) - 1:
                return [result_dict[current_prefix + (i,)] for i in range(self.dimensions[dim_idx])]
            else:
                return [_build(dim_idx + 1, current_prefix + (i,)) for i in range(self.dimensions[dim_idx])]
                
        return _build(0, ())
