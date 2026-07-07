import os
import time
import math
import heapq

class GridMap:
    def __init__(self, width, height, grid):
        self.width = width
        self.height = height
        self.grid = grid  # 2D array: '.' or 'G' for passable, others for obstacles
        
    @staticmethod
    def load_from_file(filepath):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Map file not found: {filepath}")
            
        with open(filepath, "r") as f:
            lines = [line.strip() for line in f.readlines()]
            
        # Parse header
        map_type = ""
        height = 0
        width = 0
        map_start_idx = 0
        
        for idx, line in enumerate(lines):
            if line.startswith("type"):
                map_type = line.split()[1]
            elif line.startswith("height"):
                height = int(line.split()[1])
            elif line.startswith("width"):
                width = int(line.split()[1])
            elif line.startswith("map"):
                map_start_idx = idx + 1
                break
                
        grid = []
        for line in lines[map_start_idx:map_start_idx + height]:
            if line:
                grid.append(list(line))
                
        return GridMap(width, height, grid)

    def is_passable(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            cell = self.grid[y][x]
            # '.' and 'G' are standard passable terrain. 
            # We can also treat 'S' (Swamp) or 'W' (Water) as passable but high cost
            return cell in ('.', 'G', 'S', 'W')
        return False

    def get_base_cost(self, x, y):
        if not self.is_passable(x, y):
            return float('inf')
        cell = self.grid[y][x]
        if cell == 'S': # Swamp
            return 5.0
        elif cell == 'W': # Water
            return 8.0
        return 1.0 # Standard flat ground

    def get_congestion_multiplier(self, x, y, hour):
        # Dynamic traffic congestion depending on the hour of the day
        # For simplicity, we simulate congestion in the center and main grid axes
        if not (0 <= x < self.width and 0 <= y < self.height):
            return 1.0
            
        # Hour categories: 
        # 7-9: Morning rush hour (main horizontal and vertical axes are congested)
        # 11-13: Noon rush hour (center of the map is congested)
        # 17-19: Afternoon rush hour (broad congestion)
        # Other hours: Night/low traffic (no congestion)
        
        if 7 <= hour <= 9:
            # Major traffic on axes (simulated highways at 25%, 50%, 75% of grid size)
            if abs(y - self.height // 2) < 5 or abs(x - self.width // 2) < 5:
                return 4.0
            if abs(y - self.height // 4) < 3 or abs(x - self.width // 4) < 3:
                return 3.0
        elif 11 <= hour <= 13:
            # Congestion in the central business district (CBD) - center 30% area
            dist_from_center = math.sqrt((x - self.width/2)**2 + (y - self.height/2)**2)
            max_radius = min(self.width, self.height) * 0.15
            if dist_from_center < max_radius:
                return 5.0 - (dist_from_center / max_radius) * 4.0  # cost between 1.0 and 5.0
        elif 17 <= hour <= 19:
            # Broad evening congestion
            dist_from_center = math.sqrt((x - self.width/2)**2 + (y - self.height/2)**2)
            max_radius = min(self.width, self.height) * 0.4
            if dist_from_center < max_radius:
                return 4.0
        return 1.0  # Clear traffic

    def get_cost(self, x, y, hour):
        return self.get_base_cost(x, y) * self.get_congestion_multiplier(x, y, hour)


# --- A* Algorithm and Heuristics ---

def heuristic_manhattan(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

def heuristic_euclidean(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def heuristic_chebyshev(p1, p2):
    return max(abs(p1[0] - p2[0]), abs(p1[1] - p2[1]))

def heuristic_octile(p1, p2):
    dx = abs(p1[0] - p2[0])
    dy = abs(p1[1] - p2[1])
    return (dx + dy) + (math.sqrt(2) - 2) * min(dx, dy)

def heuristic_dijkstra(p1, p2):
    return 0.0

HEURISTICS = {
    "Manhattan": heuristic_manhattan,
    "Euclidean": heuristic_euclidean,
    "Chebyshev": heuristic_chebyshev,
    "Octile": heuristic_octile,
    "Dijkstra": heuristic_dijkstra
}

def a_star_search(grid_map, start, goal, heuristic_name="Octile", hour=12):
    """
    Finds optimal path using A*
    start, goal: tuples (x, y)
    Returns: (path, cost, nodes_expanded, elapsed_time_ms)
    """
    heuristic_func = HEURISTICS.get(heuristic_name, heuristic_octile)
    
    start_time = time.perf_counter()
    
    # Priority queue: entries are (f_score, (x, y))
    # open_set tracks items currently in pq to allow checking
    pq = []
    heapq.heappush(pq, (heuristic_func(start, goal), start))
    
    came_from = {}
    g_score = {start: 0.0}
    f_score = {start: heuristic_func(start, goal)}
    
    expanded = set()
    
    # Directions: 8-way movement
    directions = [
        (1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),  # Orthogonal
        (1, 1, math.sqrt(2)), (-1, 1, math.sqrt(2)), (1, -1, math.sqrt(2)), (-1, -1, math.sqrt(2))  # Diagonal
    ]
    
    while pq:
        current_f, current = heapq.heappop(pq)
        
        if current == goal:
            # Reconstruct path
            path = []
            curr = goal
            while curr in came_from:
                path.append(curr)
                curr = came_from[curr]
            path.append(start)
            path.reverse()
            
            end_time = time.perf_counter()
            elapsed_ms = (end_time - start_time) * 1000.0
            return path, g_score[goal], len(expanded), elapsed_ms
            
        if current in expanded:
            continue
            
        expanded.add(current)
        x, y = current
        
        for dx, dy, step_weight in directions:
            nx, ny = x + dx, y + dy
            if grid_map.is_passable(nx, ny):
                # Traverse cost: step_weight (1.0 or 1.414) * grid cell cost (includes traffic)
                # We average the congestion cost of current and next cell or just use next cell cost
                cell_cost = grid_map.get_cost(nx, ny, hour)
                transition_cost = step_weight * cell_cost
                
                tentative_g = g_score[current] + transition_cost
                neighbor = (nx, ny)
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f = tentative_g + heuristic_func(neighbor, goal)
                    f_score[neighbor] = f
                    heapq.heappush(pq, (f, neighbor))
                    
    end_time = time.perf_counter()
    elapsed_ms = (end_time - start_time) * 1000.0
    return None, float('inf'), len(expanded), elapsed_ms


# --- TSP Solver (Nearest Neighbor + 2-Opt) ---

def solve_tsp_2opt(dist_matrix):
    """
    Solves TSP using Nearest Neighbor then refines with 2-Opt.
    dist_matrix: 2D list where dist_matrix[i][j] is the A* distance between node i and node j
    Node 0 is the DEPOT. The tour must start and end at node 0.
    Returns: (optimal_tour, total_cost)
    """
    n = len(dist_matrix)
    if n == 1:
        return [0, 0], 0.0
    if n == 2:
        return [0, 1, 0], dist_matrix[0][1] + dist_matrix[1][0]
        
    # 1. Initial Tour using Nearest Neighbor
    unvisited = set(range(1, n))
    tour = [0]
    current = 0
    while unvisited:
        next_node = min(unvisited, key=lambda node: dist_matrix[current][node])
        tour.append(next_node)
        unvisited.remove(next_node)
    tour.append(0)  # Return to depot
    
    def get_tour_cost(t):
        cost = 0.0
        for i in range(len(t) - 1):
            cost += dist_matrix[t[i]][t[i+1]]
        return cost

    best_tour = list(tour)
    best_cost = get_tour_cost(best_tour)
    
    # 2. 2-Opt refinement
    improved = True
    iterations = 0
    max_iterations = 1000  # Safety limit
    
    while improved and iterations < max_iterations:
        improved = False
        iterations += 1
        for i in range(1, len(best_tour) - 2):
            for j in range(i + 1, len(best_tour) - 1):
                # Try swapping segment best_tour[i...j]
                new_tour = best_tour[:]
                # Reverse the segment from i to j
                new_tour[i:j+1] = reversed(new_tour[i:j+1])
                new_cost = get_tour_cost(new_tour)
                
                if new_cost < best_cost - 1e-6:
                    best_tour = new_tour
                    best_cost = new_cost
                    improved = True
                    break
            if improved:
                break
                
    return best_tour, best_cost


# --- Runner for testing ---

def run_simulation(map_name="Berlin_1_256.map", hour=8, num_deliveries=5):
    import random
    random.seed(42) # For reproducibility
    
    script_dir = os.path.dirname(__file__)
    map_path = os.path.join(os.path.dirname(script_dir), "dataset", map_name)
    
    print("=" * 60)
    print(f"RUNNING ROUTE OPTIMIZATION SIMULATION")
    print(f"Map: {map_name}")
    print(f"Hour: {hour:02d}:00 (Congestion active)")
    print(f"Number of Delivery Locations: {num_deliveries}")
    print("=" * 60)
    
    try:
        grid_map = GridMap.load_from_file(map_path)
        print(f"Successfully loaded map. Dimensions: {grid_map.width}x{grid_map.height}")
    except Exception as e:
        print(f"Failed to load map: {e}")
        return
        
    # Find some random passable points for depot and deliveries
    passable_points = []
    # Check center areas first to find points reasonably spread out
    for y in range(20, grid_map.height - 20, 5):
        for x in range(20, grid_map.width - 20, 5):
            if grid_map.is_passable(x, y):
                passable_points.append((x, y))
                
    if len(passable_points) < num_deliveries + 1:
        print("Error: Not enough passable points in the map.")
        return
        
    selected_points = random.sample(passable_points, num_deliveries + 1)
    depot = selected_points[0]
    deliveries = selected_points[1:]
    
    all_stops = [depot] + deliveries
    n = len(all_stops)
    
    print(f"\nWarehouse Depot location: {depot}")
    for idx, d in enumerate(deliveries):
        print(f"Delivery Stop {idx+1}: {d}")
        
    # Compare Heuristics for a point-to-point path (Depot -> Stop 1)
    print("\n" + "-" * 50)
    print(f"1. HEURISTIC PERFORMANCE COMPARISON (Depot -> Stop 1)")
    print("-" * 50)
    print(f"{'Heuristic':<15} | {'Path Cost':<10} | {'Nodes Exp.':<10} | {'Time (ms)':<10}")
    print("-" * 50)
    
    goal_stop = deliveries[0]
    for h_name in HEURISTICS.keys():
        path, cost, expanded, elapsed = a_star_search(grid_map, depot, goal_stop, heuristic_name=h_name, hour=hour)
        if path:
            print(f"{h_name:<15} | {cost:<10.2f} | {expanded:<10} | {elapsed:<10.2f}")
        else:
            print(f"{h_name:<15} | {'NO PATH':<10} | {expanded:<10} | {elapsed:<10.2f}")
            
    # Now solve TSP
    print("\n" + "-" * 50)
    print(f"2. DYNAMIC ROUTING & TSP SOLVER (Using Octile Heuristic)")
    print("-" * 50)
    print("Computing distance matrix using A*...")
    
    # 2D list for distance matrix
    dist_matrix = [[0.0] * n for _ in range(n)]
    path_matrix = [[None] * n for _ in range(n)]
    
    total_astar_calls = 0
    t_start = time.perf_counter()
    
    # Fill distance matrix
    for i in range(n):
        for j in range(n):
            if i == j:
                dist_matrix[i][j] = 0.0
            else:
                path, cost, _, _ = a_star_search(grid_map, all_stops[i], all_stops[j], heuristic_name="Octile", hour=hour)
                dist_matrix[i][j] = cost
                path_matrix[i][j] = path
                total_astar_calls += 1
                
    t_end = time.perf_counter()
    print(f"Computed {total_astar_calls} A* paths in {(t_end - t_start)*1000:.2f} ms.")
    
    # Solve TSP
    tour_indices, tour_cost = solve_tsp_2opt(dist_matrix)
    
    print("\nOptimal delivery sequence:")
    sequence_str = " -> ".join([f"Stop {idx}" if idx > 0 else "DEPOT" for idx in tour_indices])
    print(sequence_str)
    print(f"Optimal Tour Total Cost (Distance/Time equivalent): {tour_cost:.2f}")
    
    # Plotting using Matplotlib if available
    try:
        import matplotlib.pyplot as plt
        import matplotlib.colors as mcolors
        
        print("\nPlotting map and route using Matplotlib...")
        fig, ax = plt.subplots(figsize=(10, 10))
        
        # Draw background grid
        # 0 for obstacle, 1 for passable, high cost paths can be colored differently
        display_grid = []
        for y in range(grid_map.height):
            row = []
            for x in range(grid_map.width):
                if not grid_map.is_passable(x, y):
                    row.append(0) # Obstacle
                else:
                    # Cost represents congestion/terrain
                    cost = grid_map.get_cost(x, y, hour)
                    row.append(cost)
            display_grid.append(row)
            
        # custom colormap: obstacles are black, passable road is light grey, high congestion is red/orange
        cmap = mcolors.LinearSegmentedColormap.from_list(
            'traffic', 
            [(0, 'black'), (0.1, '#f0f0f0'), (0.2, '#fff7bc'), (0.5, '#fec44f'), (1.0, '#d95f0e')], 
            N=256
        )
        
        # Rescale values for mapping
        max_cost = 8.0 # typical max cost for swamp or congested route
        normalized_grid = []
        for y in range(grid_map.height):
            row = []
            for x in range(grid_map.width):
                val = display_grid[y][x]
                if val == 0:
                    row.append(0.0) # Obstacles
                else:
                    # Normal road has cost 1, max is max_cost. Map cost [1..max_cost] to [0.1..1.0]
                    norm = 0.1 + 0.9 * ((min(val, max_cost) - 1.0) / (max_cost - 1.0 if max_cost > 1 else 1))
                    row.append(norm)
            normalized_grid.append(row)
            
        ax.imshow(normalized_grid, cmap=cmap, origin='upper')
        
        # Plot full tour paths
        for idx in range(len(tour_indices) - 1):
            u, v = tour_indices[idx], tour_indices[idx+1]
            path = path_matrix[u][v]
            if path:
                px = [p[0] for p in path]
                py = [p[1] for p in path]
                # draw line connecting points
                ax.plot(px, py, color='#00d2ff', linewidth=2.5, alpha=0.9, zorder=2)
                
        # Draw stops
        # Depot: gold
        ax.scatter(depot[0], depot[1], color='#ffd700', edgecolor='black', s=150, marker='*', label='DEPOT (Warehouse)', zorder=5)
        # Deliveries: purple/red
        dxs = [d[0] for d in deliveries]
        dys = [d[1] for d in deliveries]
        ax.scatter(dxs, dys, color='#9b5de5', edgecolor='black', s=100, marker='o', label='Delivery Stops', zorder=4)
        
        # Label delivery stops
        for i, d in enumerate(deliveries):
            ax.annotate(str(i+1), (d[0]+2, d[1]+2), fontsize=12, fontweight='bold', bbox=dict(boxstyle="circle,pad=0.2", fc="white", ec="purple", lw=1))
            
        plt.title(f"A* Route Optimization & TSP Solver\nMap: {map_name} | Hour: {hour:02d}:00 | Cost: {tour_cost:.2f}", fontsize=14, fontweight='bold')
        plt.legend(loc='upper right')
        
        # Save output image
        output_img = os.path.join(os.path.dirname(script_dir), "dataset", f"route_output_{hour}h.png")
        plt.savefig(output_img, dpi=150, bbox_inches='tight')
        print(f"Route map visualization saved to: {output_img}")
        
    except ImportError:
        print("\n[NOTE] Matplotlib not installed. Skipping GUI route map plotting.")
    except Exception as e:
        print(f"Error during plotting: {e}")

if __name__ == "__main__":
    run_simulation(hour=8, num_deliveries=6)
