import search
import random
import math
import itertools
import heapq
import collections

# !!! UPDATE THESE IDs BEFORE SUBMITTING !!!
ids = ["111111111", "111111111"]


class RobotNavigationProblem(search.Problem):
	"""
	This class implements the robot navigation problem according to the specifications.
	It includes optimizations for state representation and heuristics.
	"""

	def __init__(self, initial):
		# 1. Parse the Map
		self.map_grid = initial['map']
		self.rows = len(self.map_grid)
		self.cols = len(self.map_grid[0])
		self.destination = None

		# Define constants
		DESTINATION = 'D'

		for r in range(self.rows):
			for c in range(self.cols):
				if self.map_grid[r][c] == DESTINATION:
					self.destination = (r, c)
					break

				# 2. Parse Robot Config
		robot_conf = initial['robot']
		# Convert list coords to tuples (Safe for all problems)
		self.start_loc = tuple(robot_conf['starting_location'])
		self.start_battery = robot_conf['starting_moves_left']
		self.max_battery = robot_conf['maximum_moves_left_possible']
		self.robovac_damage = robot_conf['robovac_battery_damage']
		self.uneven_penalty = robot_conf['uneven_floor_penalty']

		# 3. Robovacs: Pre-process path cycles
		self.robovacs = []
		for name, path in initial['robovacs'].items():
			path_len = len(path)
			cycle_len = 2 * (path_len - 1) if path_len > 1 else 1
			self.robovacs.append({
				'path': path,
				'len': path_len,
				'cycle': cycle_len
			})

		# 4. Charging Stations
		self.charging_stations = []
		for station in initial['charging_stations']:
			# Create deep copy and force location to tuple
			s_copy = station.copy()
			s_copy['location'] = tuple(station['location'])
			self.charging_stations.append(s_copy)

		# Map location -> index for O(1) access
		self.charger_map = {s['location']: i for i, s in enumerate(self.charging_stations)}

		# The state will hold a tuple of "time when available"
		station_cooldowns = tuple([0] * len(self.charging_stations))

		# 5. Uneven Floors
		# Convert list of lists to set of tuples for O(1) lookup
		self.uneven_floors = set(tuple(x) for x in initial['uneven_floor'])

		# 6. Pre-compute Static BFS Distances for Heuristic
		self.static_distances = self._compute_static_distances()

		# Define the Initial State
		# Format: (location(r, c), current_battery, current_time, station_cooldowns_tuple)
		initial_state = (self.start_loc, self.start_battery, 0, station_cooldowns)

		search.Problem.__init__(self, initial_state)

	def _compute_static_distances(self):
		"""
		Runs a backward BFS from the destination to every passable tile.
		Returns a dictionary: loc -> distance_to_goal
		This accounts for walls ('I') in the heuristic calculation.
		"""
		distances = {self.destination: 0}
		queue = collections.deque([self.destination])

		while queue:
			r, c = queue.popleft()
			for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
				nr, nc = r + dr, c + dc
				if 0 <= nr < self.rows and 0 <= nc < self.cols and self.map_grid[nr][nc] != 'I':
					if (nr, nc) not in distances:
						distances[(nr, nc)] = distances[(r, c)] + 1
						queue.append((nr, nc))
		return distances

	def get_robovac_location(self, robovac_idx, time):
		"""Calculates the deterministic position of a robovac at a specific time."""
		r_data = self.robovacs[robovac_idx]
		path = r_data['path']

		if r_data['len'] == 1:
			return path[0]

		# "Ping-Pong" Cycle Logic: 2 * (N - 1)
		m = time % r_data['cycle']
		if m < r_data['len']:
			return path[m]
		else:
			# Retracing back
			return path[r_data['cycle'] - m]

	def get_robovac_damage(self, loc, time):
		"""Helper to calculate total damage at a location at a specific time."""
		damage = 0
		for i in range(len(self.robovacs)):
			if self.get_robovac_location(i, time) == loc:
				damage += self.robovac_damage
		return damage

	def actions(self, state):
		"""
		Return the valid actions that can be executed in the given state.
		Actions: "finish", "charge", "wait", ("move", (r,c))
		"""
		loc, bat, time, cooldowns = state
		next_time = time + 1

		# 1. Action: Finish
		if loc == self.destination:
			yield "finish"

		# 2. Action: Charge
		if loc in self.charger_map:
			idx = self.charger_map[loc]
			# Check cooldown
			if time >= cooldowns[idx]:
				charge_amt = self.charging_stations[idx]['charge_amount']
				expected_bat = min(self.max_battery, bat + charge_amt)

				# Check survival (Robovacs hit AFTER action)
				damage = self.get_robovac_damage(loc, next_time)
				if expected_bat - damage >= 0:
					yield "charge"

		# 3. Action: Wait
		wait_damage = self.get_robovac_damage(loc, next_time)
		if bat - wait_damage >= 0:
			yield "wait"

		# 4. Action: Move
		r, c = loc
		moves = [(r, c + 1), (r, c - 1), (r + 1, c), (r - 1, c)]
		for new_r, new_c in moves:
			# Check Map Bounds and Impassable 'I'
			if 0 <= new_r < self.rows and 0 <= new_c < self.cols and self.map_grid[new_r][new_c] != 'I':
				next_loc = (new_r, new_c)
				move_cost = 1

				# Uneven Floor Logic (Replacement Cost)
				curr_uneven = loc in self.uneven_floors
				next_uneven = next_loc in self.uneven_floors
				if curr_uneven or next_uneven:
					move_cost = self.uneven_penalty

				# Check Battery & Survival
				if bat >= move_cost:
					move_damage = self.get_robovac_damage(next_loc, next_time)
					if bat - move_cost - move_damage >= 0:
						yield ("move", next_loc)

	def result(self, state, action):
		"""Return the state that results from executing the given action."""
		loc, bat, time, cooldowns = state

		# Handle Finish
		if action == "finish":
			return "GOAL"

		# Initialize next state variables
		next_loc = loc
		next_bat = bat
		next_time = time + 1

		# Optimization: Reuse tuple if cooldowns don't change
		next_cooldowns = cooldowns

		# Apply Action Effects
		if action == "charge":
			idx = self.charger_map[loc]
			charge_amt = self.charging_stations[idx]['charge_amount']
			wait_dur = self.charging_stations[idx]['charge_wait']

			next_bat = min(self.max_battery, next_bat + charge_amt)

			# Update cooldowns (Only construct list here)
			temp_cd = list(cooldowns)
			temp_cd[idx] = next_time + wait_dur
			next_cooldowns = tuple(temp_cd)

		elif action == "wait":
			pass

		elif isinstance(action, tuple) and action[0] == "move":
			next_loc = action[1]
			move_cost = 1

			curr_uneven = loc in self.uneven_floors
			next_uneven = next_loc in self.uneven_floors
			if curr_uneven or next_uneven:
				move_cost = self.uneven_penalty

			next_bat -= move_cost

		# Apply Robovac Damage
		damage = self.get_robovac_damage(next_loc, next_time)
		next_bat -= damage

		# Safety floor for battery state
		if next_bat < 0:
			next_bat = -1

		return (next_loc, next_bat, next_time, next_cooldowns)

	def goal_test(self, state):
		"""Return True if the state is a goal state."""
		return state == "GOAL"

	def h(self, node):
		"""
		Heuristic: Static BFS distance + Battery Pruning.
		"""
		state = node.state
		if state == "GOAL":
			return 0

		loc = state[0]
		bat = state[1]

		# 1. Use pre-computed BFS distance
		dist = self.static_distances.get(loc, float('inf'))

		# 2. Battery Pruning
		# If battery is less than the physical distance to goal,
		# we must charge. If no chargers exist, it's impossible.
		if bat < dist and not self.charging_stations:
			return float('inf')

		return dist


def create_robot_navigation_problem(game):
	return RobotNavigationProblem(game)


def astar_search(problem, heuristic):
	"""
	Optimized A* Search using heapq for O(log N) performance.
	"""
	node = search.Node(problem.initial)
	if problem.goal_test(node.state):
		return node

	# Heap stores tuples: (f_score, tie_breaker, node)
	frontier = []
	counter = itertools.count()

	f_score = node.path_cost + heuristic(node)
	heapq.heappush(frontier, (f_score, next(counter), node))

	reached = {problem.initial: node}

	while frontier:
		_, _, node = heapq.heappop(frontier)

		if problem.goal_test(node.state):
			return node

		for child in node.expand(problem):
			s = child.state

			if s not in reached or child.path_cost < reached[s].path_cost:
				reached[s] = child

				f = child.path_cost + heuristic(child)
				heapq.heappush(frontier, (f, next(counter), child))

	return None
