import time as t

import search
import random
import math
import itertools

ids = ["345599682", "212291249"]

# Map cell types
PASSABLE = 'P'
IMPASSABLE = 'I'
DESTINATION = 'D'


class RobotNavigationProblem(search.Problem):
	"""This class implements a medical problem according to problem description file"""

	def __init__(self, initial):
		# Parse the Map
		self.map_grid = initial['map']
		self.rows = len(self.map_grid)
		self.cols = len(self.map_grid[0])
		self.destination = None

		for r in range(self.rows):
			for c in range(self.cols):
				if self.map_grid[r][c] == DESTINATION:
					self.destination = (r, c)
					break  # Found destination

		# Parse Robot Config
		robot_conf = initial['robot']
		self.start_loc = tuple(robot_conf['starting_location'])
		self.start_battery = robot_conf['starting_moves_left']
		self.max_battery = robot_conf['maximum_moves_left_possible']
		self.robovac_damage = robot_conf['robovac_battery_damage']
		self.uneven_penalty = robot_conf['uneven_floor_penalty']

		# Store robovacs with pre-processed path cycle lengths
		self.robovacs = []
		for name, path in initial['robovacs'].items():
			path_len = len(path)
			cycle_len = 2 * (path_len - 1) if path_len > 1 else 1
			self.robovacs.append({
				'path': path,
				'len': path_len,
				'cycle': cycle_len
			})

		# Store charging stations as a list of dicts to access by index
		self.charging_stations = list(initial['charging_stations'])
		for station in self.charging_stations:
			station['location'] = tuple(station['location'])

		# The state will hold a tuple of "time when available"
		# Initial state: all stations available at time 0
		station_cooldowns = tuple([0] * len(self.charging_stations))

		self.uneven_floors = set(tuple(x) for x in initial['uneven_floor'])

		# Define the initial state with format (location(r, c), current_battery, current_time, station_cooldowns_tuple)
		initial_state = (self.start_loc, self.start_battery, 0, station_cooldowns)

		search.Problem.__init__(self, initial_state)

	def get_robovac_location(self, robovac_idx, time):
		"""Calculates robovac location at specific time"""

		r_data = self.robovacs[robovac_idx]
		path = r_data['path']
		if r_data['len'] == 1:
			return path[0]

		# Calculate index in the ping-pong sequence
		m = time % r_data['cycle']
		if m < r_data['len']:
			return path[m]
		else:
			return path[r_data['cycle'] - m]

	def get_robovac_damage(self, target_loc, next_t):
		""" Helper to calculate overall Robovac damage at a specific location at time + 1 """
		damage = 0
		for i in range(len(self.robovacs)):
			if self.get_robovac_location(i, next_t) == target_loc:
				damage += self.robovac_damage
		return damage

	def actions(self, state):
		"""Return the valid actions that can be executed in the given state."""

		loc, bat, time, cooldowns = state  # Unpack state

		# Action: Finish
		if loc == self.destination:
			yield "finish"

		# Action: Charge
		for i, charging_station in enumerate(self.charging_stations):
			# If there is a station here and it's off cooldown
			if charging_station['location'] == loc and time >= cooldowns[i]:
				charge_amount = self.charging_stations[i]['charge_amount']
				# Calculate potential battery after charge
				expected_bat = min(self.max_battery, bat + charge_amount)
				# Check survival if robovacs hit after the action
				damage = self.get_robovac_damage(loc, time + 1)

				if expected_bat - damage >= 0:
					yield "charge"

		# Action: Wait
		wait_damage = self.get_robovac_damage(loc, time + 1)
		if bat - wait_damage >= 0:
			yield "wait"

		# Action: Move
		r, c = loc
		moves = [(r, c + 1), (r, c - 1), (r + 1, c), (r - 1, c)]
		for new_r, new_c in moves:
			# Bounds check and Impassable check
			if 0 <= new_r < self.rows and 0 <= new_c < self.cols and self.map_grid[new_r][new_c] != IMPASSABLE:
				next_loc = (new_r, new_c)
				move_cost = 1  # Default movement cost

				# Calculate movement cost considering uneven floor penalty
				curr_uneven = loc in self.uneven_floors
				next_uneven = next_loc in self.uneven_floors

				# Penalty applies if moving into or out of uneven floor or both
				if curr_uneven or next_uneven:
					move_cost = self.uneven_penalty

				move_damage = self.get_robovac_damage(next_loc, time + 1)  # Robovac damage after move

				# Check survival after the move
				if bat - move_cost - move_damage >= 0:
					yield "move", next_loc

	def result(self, state, action):
		"""Return the state that results from executing the given action in the given state."""

		loc, bat, time, cooldowns = state

		if action == "finish":
			return (-1, -1), bat, time + 1, cooldowns  # Goal state reached

		# Initialize next state variables
		next_loc = loc
		next_bat = bat
		next_time = time + 1
		next_cooldowns = cooldowns  # Copy to modify

		if action == "charge":
			# Find the station at current location and apply charge and cooldown updates
			for i, station in enumerate(self.charging_stations):
				if station['location'] == loc:
					charge_amt = station['charge_amount']
					wait_dur = station['charge_wait']

					# Apply charge to battery
					next_bat = min(self.max_battery, next_bat + charge_amt)

					# Update cooldown for this station
					next_cooldowns = list(next_cooldowns)  # Convert to list for mutability
					next_cooldowns[i] = next_time + wait_dur
					next_cooldowns = tuple(next_cooldowns)  # Convert back to tuple
					break  # Only one station can be at this location

		elif action == "wait":
			pass  # No location change, no battery cost, no cooldown change

		elif isinstance(action, tuple) and action[0] == "move":
			next_loc = action[1]
			move_cost = 1  # Default cost

			# Uneven Floor Logic
			curr_uneven = loc in self.uneven_floors
			next_uneven = next_loc in self.uneven_floors

			# Penalty applies if moving into or out of uneven floor
			if curr_uneven or next_uneven:
				move_cost = self.uneven_penalty

			next_bat -= move_cost

		# Apply Robovac damage
		damage = self.get_robovac_damage(next_loc, next_time)
		next_bat -= damage

		# We do not clip battery to 0 here because actions() handles validity.
		return next_loc, next_bat, next_time, next_cooldowns

	def goal_test(self, state):
		"""Return True if the state is a goal state."""
		return state[0] == (-1, -1)

	def h(self, node):
		"""
        Heuristic function for A* search.
        Estimates the minimum number of moves needed to reach the goal.
        """

		if self.goal_test(node.state):
			return 0

		loc = node.state[0]

		# Using Manhattan distance as heuristic
		return abs(loc[0] - self.destination[0]) + abs(loc[1] - self.destination[1])


def create_robot_navigation_problem(game):
	return RobotNavigationProblem(game)


def astar_search(problem, heuristic):
	"""A* search algorithm implementation."""

	start_time = t.time() # Start time for timeout tracking

	expansion_count = 0
	MAX_EXPANSIONS = 150000  # Memory Limit Check

	# Create the initial node
	node = search.Node(problem.initial)

	# Check if initial state is already the goal
	if problem.goal_test(node.state):
		return node

	# PriorityQueue ordered by f(n) = g(n) + h(n) that pops the node with the lowest f-score first.
	frontier = search.PriorityQueue(min, lambda n: n.path_cost + heuristic(n))
	frontier.append(node)

	# Keeps track of the best path found so far to any state.
	reached = {problem.initial: node}

	while frontier:
		if t.time() - start_time > 60:
			return None  # Timeout after 60 seconds

		# We stop early if the search gets too big, avoiding the crash.
		if expansion_count > MAX_EXPANSIONS:
			return None

		node = frontier.pop()
		expansion_count += 1

		if problem.goal_test(node.state):
			return node

		# Expand node
		for child in node.expand(problem):
			s = child.state

			# If state is new, or we found a cheaper path to this state
			if s not in reached or child.path_cost < reached[s].path_cost:
				reached[s] = child
				frontier.append(child)

	return None


def astar_search2(problem, heuristic):
	"""
	A* Search using search.PriorityQueue with Battery Dominance Pruning.
	"""

	start_time = t.time() # Start time for timeout tracking

	expansion_count = 0
	MAX_EXPANSIONS = 150000  # Memory Limit Check

	node = search.Node(problem.initial)
	if problem.goal_test(node.state):
		return node

	# PriorityQueue from utils.py
	frontier = search.PriorityQueue(min, lambda n: n.path_cost + heuristic(n))
	frontier.append(node)

	# DOMINANCE TABLE (Replaces standard 'reached')
	# Key: (loc, time, cooldowns) -> Value: max_battery_seen
	# This acts as our "Closed Set". We only re-visit a state context if we found
	# a way to get there with MORE battery.
	reached_dominance = {}

	s0 = problem.initial
	key0 = (s0[0], s0[2], s0[3])  # (loc, time, cooldowns)
	reached_dominance[key0] = s0[1]

	while frontier:
		if t.time() - start_time > 60:
			return None  # Timeout after 60 seconds

		# We stop early if the search gets too big, avoiding the crash.
		if expansion_count > MAX_EXPANSIONS:
			return None

		node = frontier.pop()
		expansion_count += 1

		if problem.goal_test(node.state):
			return node

		for child in node.expand(problem):
			s = child.state
			loc, bat, time, cooldowns = s

			# Context Key: Everything except battery
			dom_key = (loc, time, cooldowns)

			# DOMINANCE CHECK:
			# If we have reached this context before with BETTER (or equal) battery,
			# then 'child' is a suboptimal path. Prune it.
			if dom_key in reached_dominance and bat <= reached_dominance[dom_key]:
				continue

			# Otherwise, this path offers more battery than any previous path
			# to this specific spot at this specific time. Keep it!
			reached_dominance[dom_key] = bat
			frontier.append(child)

	return None
