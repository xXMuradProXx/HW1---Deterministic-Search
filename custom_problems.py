custom_problems = [
	# ---------------------------------------------------------
	# Problem 1: "The Toll Road" (Uneven Floor Trap)
	# Testing: Uneven Floor Penalty logic.
	# Scenario: The top path (row 0) is direct but has uneven floors.
	# The penalty is high (5). The robot starts with 10 battery.
	# Going top: (0,0)->(0,1) [Enter Uneven, Cost 5] -> (0,2) [Move Uneven, Cost 1] -> (0,3) [Exit Uneven, Cost 5]. Total: 11.
	# Result: Robot dies if it takes the short path. It MUST take the long bottom path.
	# ---------------------------------------------------------
	{
		"map": [
			['P', 'P', 'P', 'D'],
			['P', 'I', 'I', 'P'],
			['P', 'P', 'P', 'P'],
		],
		"robot": {
			"starting_location": (0, 0),
			"starting_moves_left": 10,  # Not enough for top path (needs 11)
			"robovac_battery_damage": 0,
			"uneven_floor_penalty": 5,  # High penalty
			"maximum_moves_left_possible": 20
		},
		"robovacs": {},
		"charging_stations": [],
		"uneven_floor": [(0, 1), (0, 2)],  # The "Toll Road"
	},

	# ---------------------------------------------------------
	# Problem 2: "The Charging Ambush"
	# Testing: Robovac survival check AFTER charging.
	# Scenario: Robot has 1 battery. Must charge at (0,1) to reach goal.
	# A Robovac patrols the charging station.
	# If Robot moves (0,0)->(0,1) immediately, it charges to 6, but Robovac hits it for 10 damage.
	# 6 - 10 < 0. Robot dies.
	# Solution: Robot must WAIT at (0,0) for the Robovac to leave, then move and charge.
	# ---------------------------------------------------------
	{
		"map": [
			['P', 'P', 'D'],
		],
		"robot": {
			"starting_location": (0, 0),
			"starting_moves_left": 1,
			"robovac_battery_damage": 10,  # Lethal damage
			"uneven_floor_penalty": 2,
			"maximum_moves_left_possible": 10
		},
		"robovacs": {
			# Robovac moves (0,1) -> (0,2) -> (0,1)
			# t=0: (0,1). t=1: (0,2). t=2: (0,1).
			# If Robot moves at t=0, it arrives t=1. Charges.
			# Robovac arrives t=2? No, check cycle.
			# Path len 2. Cycle len 2*(2-1) = 2.
			# t=0: (0,1). t=1: (0,2). t=2: (0,1).
			# If Robot Moves t=0 -> Arrives (0,1) at t=1. Safe (Robovac at 0,2).
			# Robot Charges t=1 -> Finishes t=2. Robovac arrives (0,1) at t=2. BAM.
			"guardian": [(0, 1), (0, 2)]
		},
		"charging_stations": [{"location": (0, 1), "charge_amount": 5, "charge_wait": 0}],
		"uneven_floor": [],
	},

	# ---------------------------------------------------------
	# Problem 3: "The Doorman" (Goal Blocking)
	# Testing: Waiting at the doorstep.
	# Scenario: The destination is at (0,2).
	# A Robovac sits on (0,2) at t=2.
	# Robot Path: (0,0) -> (0,1) -> (0,2). Arrives at t=2.
	# If Robot walks straight in, it hits Robovac at (0,2) and takes lethal damage.
	# Solution: Move to (0,1), WAIT 1 turn, then move to D.
	# ---------------------------------------------------------
	{
		"map": [
			['P', 'P', 'D'],
		],
		"robot": {
			"starting_location": (0, 0),
			"starting_moves_left": 5,
			"robovac_battery_damage": 10,
			"uneven_floor_penalty": 2,
			"maximum_moves_left_possible": 10
		},
		"robovacs": {
			# Path len 2. Cycle 2.
			# t=0: (0,3), t=1: (0,2), t=2: (0,3)... wait let's adjust to hit t=2.
			# We want Robovac at (0,2) when Robot arrives at t=2.
			# Path: [(0,3), (0,2)].
			# t=0: (0,3). t=1: (0,2). t=2: (0,3). This misses.
			# Let's try Path: [(0,2), (0,3)].
			# t=0: (0,2). t=1: (0,3). t=2: (0,2). HIT!
			"doorman": [(0, 2), (0, 3)]
		},
		"charging_stations": [],
		"uneven_floor": [],
	},

	# ---------------------------------------------------------
	# Problem 4: "Exact Change Only" (Zero Sum Game)
	# Testing: Battery going exactly to 0.
	# Scenario: Path is 4 steps. Battery is 4.
	# There is a Robovac that does 1 damage on the optimal path.
	# If Robot gets hit, it has 3 battery -> fails.
	# Robot must time it perfectly to avoid the hit, arriving with exactly 0 battery.
	# ---------------------------------------------------------
	{
		"map": [
			['P', 'P', 'P', 'P', 'D'],
		],
		"robot": {
			"starting_location": (0, 0),
			"starting_moves_left": 4,  # Distance to goal is 4
			"robovac_battery_damage": 1,  # Just enough to kill the run
			"uneven_floor_penalty": 2,
			"maximum_moves_left_possible": 10
		},
		"robovacs": {
			# Robot path: (0,0)->(0,1)->(0,2)->(0,3)->(0,4)
			# Arrives at: t=1,   t=2,   t=3,   t=4
			# We put a robovac at (0,2) at t=2.
			# Path len 3: [(0,2), (0,1), (0,2)]?? No.
			# Let's use simple vertical crossing.
			# Map is 1D? Let's make it 2D so Robovac can cross.
			# Actually, let's keep it 1D and force a Wait.
			# If Robot waits, it burns 0 battery but 1 turn.
			# BUT: Wait does not consume battery. So Robot CAN wait to avoid damage.
			# The test is: Does your code allow finishing with 0 battery?
			"crosser": [(0, 2), (0, 3)]
			# t=0:(0,2), t=1:(0,3), t=2:(0,2).
			# Robot arrives (0,2) at t=2 -> BAM.
			# Robot must Wait at t=0 or t=1.
		},
		"charging_stations": [],
		"uneven_floor": [],
	}
]

tricky_problems = [
    # ---------------------------------------------------------
    # Problem 1: "The Lava Walk" (Uneven Floor Exception)
    # Edge Case: Moving between two uneven tiles.
    # [cite_start]Rule: "Moving from one uneven floor tile to another does not carry extra penalty" [cite: 50]
    # Scenario: The path is mostly uneven tiles.
    # Path: (0,0)[U] -> (0,1)[U] -> (0,2)[U] -> (0,3)[P] -> (0,4)[D]
    # Costs:
    # 1. (0,0)->(0,1): Uneven->Uneven. Cost = 1.
    # 2. (0,1)->(0,2): Uneven->Uneven. Cost = 1.
    # 3. (0,2)->(0,3): Uneven->Passable. Cost = Penalty (5).
    # 4. (0,3)->(0,4): Passable->Passable. Cost = 1.
    # Total Required: 1 + 1 + 5 + 1 = 8.
    # Start Battery: 8.
    # TRAP: If your code adds penalty for U->U, cost will be 5+5+5+1 = 16. Fails.
    # ---------------------------------------------------------
    {
        "map": [
            ['P', 'P', 'P', 'P', 'D'],
        ],
        "robot": {
            "starting_location": (0, 0),
            "starting_moves_left": 8,
            "robovac_battery_damage": 0,
            "uneven_floor_penalty": 5,
            "maximum_moves_left_possible": 20
        },
        "robovacs": {},
        "charging_stations": [],
        "uneven_floor": [(0, 0), (0, 1), (0, 2)],
    },

    # ---------------------------------------------------------
    # Problem 2: "The Overflow" (Battery Cap)
    # Edge Case: Charging exceeds maximum capacity.
    # [cite_start]Rule: "It is not possible to charge the battery above its capacity" [cite: 37]
    # Scenario: Start with 1. Max is 5. Station gives 100.
    # Move (0,0)->(0,1) [Cost 1]. Bat = 0.
    # Charge at (0,1). Bat = min(5, 0+100) = 5.
    # Path remaining: 5 steps.
    # TRAP: If you charge to 100, you finish easily with 95 left.
    # If you cap correctly at 5, you finish with exactly 0 left.
    # ---------------------------------------------------------
    {
        "map": [
            ['P', 'P', 'P', 'P', 'P', 'P', 'D'], # 7 tiles total. 0 to 6.
        ],
        "robot": {
            "starting_location": (0, 0),
            "starting_moves_left": 1,
            "robovac_battery_damage": 0,
            "uneven_floor_penalty": 2,
            "maximum_moves_left_possible": 5 # Strict Cap
        },
        "robovacs": {},
        "charging_stations": [{"location": (0, 1), "charge_amount": 100, "charge_wait": 0}],
        "uneven_floor": [],
    },

    # ---------------------------------------------------------
    # Problem 3: "The Double Dip" (Station Cooldown)
    # Edge Case: Trying to use a station while it's refueling.
    # [cite_start]Rule: "station being inactive for a certain number of turns" [cite: 36]
    # Scenario: Robot needs to charge TWICE at the same station.
    # Station at (0,0). Goal at (0,2).
    # Start Bat 0. Charge(+2) -> Move(0,1) -> Move(0,0) -> Charge(+2) -> Move(0,1)-> Move(0,2).
    # Cooldown is 5 turns.
    # Robot charges at t=0. Active again at t = 0 + 1 (action) + 5 (wait) = 6.
    # Robot returns to (0,0) quickly. Must WAIT until t=6 to charge again.
    # ---------------------------------------------------------
    {
        "map": [
            ['P', 'P', 'D'],
        ],
        "robot": {
            "starting_location": (0, 0),
            "starting_moves_left": 0,
            "robovac_battery_damage": 0,
            "uneven_floor_penalty": 2,
            "maximum_moves_left_possible": 10
        },
        "robovacs": {},
        "charging_stations": [{"location": (0, 0), "charge_amount": 2, "charge_wait": 5}],
        "uneven_floor": [],
    },

    # ---------------------------------------------------------
    # Problem 4: "The Cycle Master" (Complex Robovac Math)
    # Edge Case: Robovac cycle calculation logic.
    # Path: [(0,1), (0,2), (0,3), (0,4)]. Len 4.
    # Cycle: 0,1,2,3, 2,1. Length = 2*(4-1) = 6.
    # Sequence: 1, 2, 3, 4, 3, 2 | 1, 2...
    # Robot must cross (0,2) safely.
    # Robovac is at (0,2) at indices: 1, 5, 7, 11...
    # Robot starts (0,0). Moves -> (0,1) -> (0,2). Arrives t=2.
    # Robovac at t=2 is at index 2 -> (0,3). Safe?
    # Wait, sequence is: t0=(0,1), t1=(0,2), t2=(0,3).
    # Robot arrives (0,2) at t=2. Robovac is at (0,3). Safe.
    # Let's shift Robovac so it HITS at t=2.
    # We want Robovac at (0,2) at t=2.
    # This happens if sequence starts differently? No, fixed path.
    # Let's force a wait by blocking the destination.
    # Destination (0,2). Robot arrives t=2.
    # Robovac needs to be at (0,2) at t=2.
    # Path: [(0,2), (0,3), (0,4)].
    # t0=(0,2), t1=(0,3), t2=(0,2). HIT.
    # Robot must Wait 1 turn (arrive t=3).
    # At t=3, Robovac is at (0,3). (2->3->2->3). Safe.
    # ---------------------------------------------------------
    {
        "map": [
            ['P', 'P', 'D'],
        ],
        "robot": {
            "starting_location": (0, 0),
            "starting_moves_left": 5,
            "robovac_battery_damage": 10,
            "uneven_floor_penalty": 2,
            "maximum_moves_left_possible": 10
        },
        "robovacs": {
            "math_test": [(0, 2), (0, 3), (0, 4)]
        },
        "charging_stations": [],
        "uneven_floor": [],
    }
]

hard_problems = [
    # ---------------------------------------------------------
    # Problem 1: "The Resource Run" (Backtracking Test)
    # Difficulty: Hard
    # Description: The goal is to the East (Right). The heuristic says "Go Right".
    # However, the robot has 0 battery. There is a charger to the West (Left).
    # The robot must move AWAY from the goal to charge, then come back.
    # This tests if your A* can handle increasing h(n) temporarily to lower g(n) later.
    # ---------------------------------------------------------
    {
        "map": [
            ['P', 'P', 'P', 'P', 'P', 'D'],
        ],
        "robot": {
            "starting_location": (0, 2), # Start in middle
            "starting_moves_left": 0,    # Dead battery
            "robovac_battery_damage": 0,
            "uneven_floor_penalty": 2,
            "maximum_moves_left_possible": 20
        },
        "robovacs": {},
        "charging_stations": [{"location": (0, 0), "charge_amount": 10, "charge_wait": 0}], # Charger at far left
        "uneven_floor": [],
    },

    # ---------------------------------------------------------
    # Problem 2: "The Expensive Shortcut" (Heuristic Trap)
    # Difficulty: Hard
    # Description: There are two paths to the goal.
    # 1. The "Straight" path: Short distance (Manhattan optimal), but filled with Uneven Floors (High Cost).
    # 2. The "Detour": Goes way around. Long distance, but cheap (Smooth floor).
    # The robot has just enough battery for the Detour, but NOT for the Straight path.
    # A* will naturally try the straight path first. It must realize it's a dead end (battery death)
    # and backtrack to explore the massive detour.
    # ---------------------------------------------------------
    {
        "map": [
            ['P', 'P', 'P', 'P', 'D'], # Row 0: Short path (Indices 0,1,2,3,4)
            ['P', 'I', 'I', 'I', 'P'], # Row 1: Wall
            ['P', 'P', 'P', 'P', 'P'], # Row 2: Detour
        ],
        "robot": {
            "starting_location": (0, 0),
            "starting_moves_left": 10,
            "robovac_battery_damage": 0,
            "uneven_floor_penalty": 5, # Huge penalty
            "maximum_moves_left_possible": 20
        },
        "robovacs": {},
        "charging_stations": [],
        # The straight path (Row 0) is all uneven.
        # Moving (0,0)->(0,1) costs 5. (0,1)->(0,2) costs 1. (0,2)->(0,3) costs 1. (0,3)->(0,4) costs 5.
        # Total straight cost = 12. Battery = 10. Fails.
        # Detour: Down to (2,0), across to (2,4), up to (0,4).
        # Cost: 2 down + 4 across + 2 up = 8. Battery = 10. Success.
        "uneven_floor": [(0, 1), (0, 2), (0, 3)],
    },

    # ---------------------------------------------------------
    # Problem 3: "The Synchronized Dance" (Timing Test)
    # Difficulty: Very Hard
    # Description: The robot must cross a 3x3 room.
    # Rows 1 and 2 are patrolled by Robovacs moving horizontally.
    # They are synced such that the robot must Move-Wait-Move-Wait to pass safely.
    # If the robot just rushes, it gets hit.
    # ---------------------------------------------------------
    {
        "map": [
            ['P', 'P', 'P'],
            ['P', 'P', 'P'],
            ['P', 'P', 'D'],
        ],
        "robot": {
            "starting_location": (0, 0),
            "starting_moves_left": 10,
            "robovac_battery_damage": 10, # Lethal
            "uneven_floor_penalty": 2,
            "maximum_moves_left_possible": 10
        },
        "robovacs": {
            # Row 0 is safe.
            # Row 1 has a Robovac patrolling (1,0)<->(1,2).
            # Row 2 has a Robovac patrolling (2,0)<->(2,2).
            # We offset them so the robot gets trapped if it's too fast.
            "guard_1": [(1, 0), (1, 1), (1, 2)],
            "guard_2": [(2, 2), (2, 1), (2, 0)]  # Moves opposite
        },
        "charging_stations": [],
        "uneven_floor": [],
    },

    # ---------------------------------------------------------
    # Problem 4: "The Recharge Loop" (Cooldown Management)
    # Difficulty: Hard
    # Description: The robot starts with 0 battery.
    # There is a charger at start.
    # It must charge, but the charger gives VERY little battery (2).
    # The goal is 6 steps away.
    # The robot must: Charge -> Wait (for cooldown) -> Charge -> Wait -> Charge -> Move.
    # This tests if your state correctly updates 'cooldowns' and allows multiple interactions.
    # ---------------------------------------------------------
    {
        "map": [
            ['P', 'P', 'P', 'P', 'P', 'P', 'D'],
        ],
        "robot": {
            "starting_location": (0, 0),
            "starting_moves_left": 0,
            "robovac_battery_damage": 0,
            "uneven_floor_penalty": 2,
            "maximum_moves_left_possible": 10
        },
        "robovacs": {},
        "charging_stations": [
            {"location": (0, 0), "charge_amount": 2, "charge_wait": 2}
        ],
        "uneven_floor": [],
    }
]

hard_large_problems = [
    # ---------------------------------------------------------
    # Problem 1: "The Great Spiral" (Heuristic Torture Test)
    # Grid: 13x13
    # Difficulty: Hard
    # Description: The robot starts at (0,0) and the goal is at (6,6) (the center).
    # However, the map is a giant spiral wall. The BFS heuristic is required to solve this quickly.
    # ---------------------------------------------------------
    {
        "map": [
            ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
            ['P', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'P'],
            ['P', 'I', 'P', 'P', 'P', 'P', 'P', 'P', 'P', 'P', 'P', 'I', 'P'],
            ['P', 'I', 'P', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'P', 'I', 'P'],
            ['P', 'I', 'P', 'I', 'P', 'P', 'P', 'P', 'P', 'I', 'P', 'I', 'P'],
            ['P', 'I', 'P', 'I', 'P', 'I', 'I', 'I', 'P', 'I', 'P', 'I', 'P'],
            ['P', 'I', 'P', 'I', 'P', 'I', 'D', 'I', 'P', 'I', 'P', 'I', 'P'], # Goal in center
            ['P', 'I', 'P', 'I', 'P', 'I', 'P', 'P', 'P', 'I', 'P', 'I', 'P'],
            ['P', 'I', 'P', 'I', 'P', 'I', 'I', 'I', 'I', 'I', 'P', 'I', 'P'],
            ['P', 'I', 'P', 'I', 'P', 'P', 'P', 'P', 'P', 'P', 'P', 'I', 'P'],
            ['P', 'I', 'P', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'P'],
            ['P', 'I', 'P', 'P', 'P', 'P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
            ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
        ],
        "robot": {
            "starting_location": (0, 0),
            "starting_moves_left": 100,
            "robovac_battery_damage": 0,
            "uneven_floor_penalty": 2,
            "maximum_moves_left_possible": 100
        },
        "robovacs": {},
        "charging_stations": [],
        "uneven_floor": [],
    },

    # ---------------------------------------------------------
    # Problem 2: "The Highway Crossing" (Timing & Scale)
    # Grid: 15x15
    # Difficulty: Hard
    # Description: Open field. Cross from (0,0) to (14,14).
    # Rows 3, 7, 11 are "Highways" patrolled by Robovacs.
    # ---------------------------------------------------------
    {
        # Define 15x15 grid with 'D' at (14,14) immediately
        "map": [
            ['P' if not (r == 14 and c == 14) else 'D' for c in range(15)]
            for r in range(15)
        ],
        "robot": {
            "starting_location": (0, 0),
            "starting_moves_left": 40,
            "robovac_battery_damage": 100, # Instant Death
            "uneven_floor_penalty": 2,
            "maximum_moves_left_possible": 50
        },
        "robovacs": {
            # Row 3: Patrolling Left-Right
            "highway_1": [(3, c) for c in range(15)],
            # Row 7: Patrolling Right-Left
            "highway_2": [(7, c) for c in range(14, -1, -1)],
            # Row 11: Patrolling Left-Right
            "highway_3": [(11, c) for c in range(15)],
        },
        "charging_stations": [],
        "uneven_floor": [],
    },

    # ---------------------------------------------------------
    # Problem 3: "The Desert Trek" (Charging & Uneven Floor)
    # Grid: 20x5 (Long horizontal strip)
    # Difficulty: Hard
    # Description: Long corridor with alternating uneven floors.
    # Must use every charging station along the way.
    # ---------------------------------------------------------
    {
        "map": [
            ['P' if c != 19 else 'D' for c in range(20)], # 0..18 Passable, 19 Goal
            ['I' for _ in range(20)], # Wall
            ['I' for _ in range(20)], # Wall
            ['I' for _ in range(20)], # Wall
            ['I' for _ in range(20)], # Wall
        ],
        "robot": {
            "starting_location": (0, 0),
            "starting_moves_left": 6,
            "robovac_battery_damage": 0,
            "uneven_floor_penalty": 5,
            "maximum_moves_left_possible": 15
        },
        "robovacs": {},
        "charging_stations": [
            {"location": (0, 4), "charge_amount": 10, "charge_wait": 0},
            {"location": (0, 9), "charge_amount": 10, "charge_wait": 0},
            {"location": (0, 14), "charge_amount": 10, "charge_wait": 0},
        ],
        "uneven_floor": [(0, c) for c in range(1, 20, 2)],
    }
]