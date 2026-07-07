import os
import time
import math
import heapq

# Khởi tạo thư mục xuất ảnh nếu chưa tồn tại
output_dir = r"d:\CNTT\TRITUENHANTAO\BTL\IMG"
os.makedirs(output_dir, exist_ok=True)

# Thử import matplotlib. Nếu chưa cài đặt, thông báo lỗi.
try:
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError:
    print("[ERROR] Matplotlib or Numpy is not installed. Please run: pip install matplotlib numpy")
    exit(1)

# ==========================================================================
# 1. THUẬT TOÁN A* LÕI & HEURISTICS (Đồng bộ với web và a_star_tsp.py)
# ==========================================================================

# Định nghĩa các hàm Heuristics
def manhattan_distance(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

def euclidean_distance(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def octile_distance(p1, p2):
    dx = abs(p1[0] - p2[0])
    dy = abs(p1[1] - p2[1])
    return (dx + dy) + (math.sqrt(2) - 2) * min(dx, dy)

def chebyshev_distance(p1, p2):
    return max(abs(p1[0] - p2[0]), abs(p1[1] - p2[1]))

def dijkstra_heuristic(p1, p2):
    return 0

HEURISTIC_FUNCS = {
    "Manhattan": manhattan_distance,
    "Euclidean": euclidean_distance,
    "Octile": octile_distance,
    "Chebyshev": chebyshev_distance,
    "Dijkstra": dijkstra_heuristic
}

# Hướng di chuyển 8 hướng
DIRECTIONS = [
    (0, 1, 1.0),    # Đông
    (1, 0, 1.0),    # Nam
    (0, -1, 1.0),   # Tây
    (-1, 0, 1.0),   # Bắc
    (1, 1, math.sqrt(2)),   # Đông Nam
    (1, -1, math.sqrt(2)),  # Tây Nam
    (-1, 1, math.sqrt(2)),  # Đông Bắc
    (-1, -1, math.sqrt(2))  # Tây Bắc
]

def a_star_search(grid, start, goal, heuristic_name="Octile"):
    """
    Thuật toán tìm kiếm A* trên lưới trọng số động
    grid: Ma trận 2D chứa trọng số di chuyển (0 đại diện cho vật cản)
    """
    height = len(grid)
    width = len(grid[0])
    heuristic_fn = HEURISTIC_FUNCS.get(heuristic_name, octile_distance)
    
    # Priority Queue chứa (f_score, g_score, (x, y))
    open_set = []
    heapq.heappush(open_set, (heuristic_fn(start, goal), 0, start))
    
    came_from = {}
    
    g_score = {start: 0}
    visited_nodes_in_order = []
    visited_set = set()
    
    while open_set:
        _, current_g, current = heapq.heappop(open_set)
        
        if current in visited_set:
            continue
        visited_set.add(current)
        visited_nodes_in_order.append(current)
        
        if current == goal:
            # Tái dựng đường đi
            path = []
            temp = current
            while temp in came_from:
                path.append(temp)
                temp = came_from[temp]
            path.append(start)
            path.reverse()
            return {
                "path": path,
                "cost": current_g,
                "visited": visited_nodes_in_order
            }
            
        x, y = current
        for dx, dy, step_cost in DIRECTIONS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                cell_weight = grid[ny][nx]
                if cell_weight == 0: # Obstacle
                    continue
                
                # Chi phí di chuyển = Trọng số ô * Khoảng cách bước (1 hoặc 1.41)
                tentative_g = current_g + cell_weight * step_cost
                neighbor = (nx, ny)
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + heuristic_fn(neighbor, goal)
                    came_from[neighbor] = current
                    heapq.heappush(open_set, (f_score, tentative_g, neighbor))
                    
    return {"path": [], "cost": float('inf'), "visited": visited_nodes_in_order}

# ==========================================================================
# 2. THUẬT TOÁN TSP (Greedy + 2-Opt)
# ==========================================================================
def solve_tsp(dist_matrix):
    n = len(dist_matrix)
    # Khởi tạo chuỗi đi tham lam (Greedy) xuất phát từ 0 (Depot)
    unvisited = set(range(1, n))
    current = 0
    tour = [0]
    
    while unvisited:
        next_node = min(unvisited, key=lambda x: dist_matrix[current][x])
        tour.append(next_node)
        unvisited.remove(next_node)
        current = next_node
    tour.append(0) # Quay về kho
    
    # Tính chi phí hiện tại
    def get_tour_cost(t):
        return sum(dist_matrix[t[i]][t[i+1]] for i in range(len(t)-1))
        
    best_tour = tour
    best_cost = get_tour_cost(best_tour)
    
    # Tối ưu hóa bằng 2-Opt
    improved = True
    while improved:
        improved = False
        for i in range(1, len(best_tour) - 2):
            for j in range(i + 1, len(best_tour) - 1):
                new_tour = best_tour[:]
                new_tour[i:j+1] = reversed(best_tour[i:j+1])
                new_cost = get_tour_cost(new_tour)
                if new_cost < best_cost:
                    best_tour = new_tour
                    best_cost = new_cost
                    improved = True
                    break
            if improved:
                break
    return best_tour, best_cost

# ==========================================================================
# 3. CHUẨN BỊ BẢN ĐỒ MẪU 32x32 (Giống hệt presets.js)
# ==========================================================================
def get_preset_32x32():
    grid = np.ones((32, 32))
    # Tạo tường bao và các khối tòa nhà chướng ngại vật
    grid[0, :] = 0
    grid[31, :] = 0
    grid[:, 0] = 0
    grid[:, 31] = 0
    
    grid[8, 5:16] = 0
    grid[8, 18:27] = 0
    grid[16, 5:13] = 0
    grid[16, 15:28] = 0
    grid[24, 8:23] = 0
    
    # Tường ngăn giữa các con phố
    grid[3:7, 14] = 0
    grid[10:15, 14] = 0
    grid[18:23, 17] = 0
    grid[18:30, 7] = 0
    grid[2:13, 24] = 0
    
    return grid

# ==========================================================================
# 4. CHỨC NĂNG XUẤT ẢNH HỌC THUẬT CHO BÁO CÁO
# ==========================================================================

# --- ẢNH 1: Sơ đồ chu trình tối ưu TSP trên bản đồ 32x32 ---
def export_route_32x32_tsp():
    print("Drawing: route_32x32_tsp.png...")
    grid = get_preset_32x32()
    
    depot = (5, 5)
    stops = [(10, 22), (25, 12), (18, 25), (28, 8)]
    all_pts = [depot] + stops
    
    # Tính ma trận khoảng cách và lưu đường dẫn
    n = len(all_pts)
    dist_matrix = [[0]*n for _ in range(n)]
    paths = [[None]*n for _ in range(n)]
    
    for i in range(n):
        for j in range(n):
            if i != j:
                res = a_star_search(grid, all_pts[i], all_pts[j], "Octile")
                dist_matrix[i][j] = res["cost"]
                paths[i][j] = res["path"]
                
    tour, tour_cost = solve_tsp(dist_matrix)
    
    # Vẽ đồ thị
    fig, ax = plt.subplots(figsize=(8, 8), dpi=150)
    
    # Vẽ chướng ngại vật màu xám đậm, đường trống màu xám nhạt
    cmap_grid = np.zeros((32, 32, 3))
    for y in range(32):
        for x in range(32):
            if grid[y, x] == 0:
                cmap_grid[y, x] = [0.2, 0.25, 0.3] # Slate gray
            else:
                cmap_grid[y, x] = [0.95, 0.96, 0.98] # Light asphalt
                
    ax.imshow(cmap_grid, origin='upper')
    
    # Vẽ lưới
    ax.set_xticks(np.arange(-0.5, 32, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, 32, 1), minor=True)
    ax.grid(which='minor', color='#cbd5e1', linestyle='-', linewidth=0.5)
    ax.tick_params(which='both', bottom=False, left=False, labelbottom=False, labelleft=False)
    
    # Vẽ các chặng đường đi nối tiếp
    for k in range(len(tour) - 1):
        u, v = tour[k], tour[k+1]
        path = paths[u][v]
        if path:
            px = [p[0] for p in path]
            py = [p[1] for p in path]
            # Vẽ đường nét liền đậm màu đỏ cam phát sáng nhẹ
            ax.plot(px, py, color='#f59e0b', linewidth=4, alpha=0.9, zorder=5)
            # Vẽ hướng đi bằng mũi tên nhỏ ở giữa chặng
            mid = len(px) // 2
            ax.annotate('', xy=(px[mid+1], py[mid+1]), xytext=(px[mid], py[mid]),
                        arrowprops=dict(arrowstyle="->", color='#ef4444', lw=2), zorder=6)
            
    # Vẽ Depot (Kho) - Ngôi sao màu vàng
    ax.scatter(depot[0], depot[1], color='#eab308', edgecolors='#0f172a', marker='*', s=350, label='Kho Depot', zorder=10)
    
    # Vẽ các điểm giao hàng - Ghim hình tròn màu tím đánh số
    for idx, (sx, sy) in enumerate(stops):
        ax.scatter(sx, sy, color='#9b5de5', edgecolors='white', marker='o', s=200, zorder=10)
        ax.text(sx, sy, str(idx+1), color='white', fontsize=10, weight='bold', ha='center', va='center', zorder=11)
        
    ax.set_title(f"Sơ đồ lộ trình tối ưu TSP trên bản đồ 32x32\n(Hành trình: Depot -> P1 -> P3 -> P2 -> P4 -> Depot | Chi phí: {tour_cost:.2f})", fontsize=11, weight='bold', pad=15)
    ax.legend(loc='upper right')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "route_32x32_tsp.png"), bbox_inches='tight')
    plt.close()
    print("Saved image: route_32x32_tsp.png")

# --- ẢNH 2: So sánh tránh kẹt xe theo giờ cao điểm sáng ---
def export_traffic_avoidance_comparison():
    print("Drawing: traffic_avoidance_comparison.png...")
    grid = get_preset_32x32()
    
    # Điểm xuất phát và đích cắt qua vùng trục chính giữa đô thị
    start = (4, 15)
    goal = (28, 15)
    
    # Kịch bản 1: Giờ thấp điểm (Không kẹt xe - cost=1)
    grid_free = grid.copy()
    res_free = a_star_search(grid_free, start, goal, "Octile")
    
    # Kịch bản 2: Giờ cao điểm sáng (Kẹt xe nghiêm trọng trục dọc giữa x=16)
    grid_jam = grid.copy()
    # Kẹt dọc từ hàng 2 đến 30 tại các cột quanh trục dọc
    grid_jam[2:30, 15:17] = 5.0 # Tăng chi phí đi lại lên x5
    res_jam = a_star_search(grid_jam, start, goal, "Octile")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7), dpi=150)
    
    def draw_scenario(ax, g, path, title, is_jam):
        cmap_grid = np.zeros((32, 32, 3))
        for y in range(32):
            for x in range(32):
                if g[y, x] == 0:
                    cmap_grid[y, x] = [0.2, 0.25, 0.3] # Vật cản
                elif g[y, x] == 5.0:
                    cmap_grid[y, x] = [0.99, 0.8, 0.8] # Vùng kẹt xe màu đỏ nhạt
                else:
                    cmap_grid[y, x] = [0.95, 0.96, 0.98] # Bình thường
                    
        ax.imshow(cmap_grid, origin='upper')
        ax.set_xticks(np.arange(-0.5, 32, 1), minor=True)
        ax.set_yticks(np.arange(-0.5, 32, 1), minor=True)
        ax.grid(which='minor', color='#cbd5e1', linestyle='-', linewidth=0.5)
        ax.tick_params(which='both', bottom=False, left=False, labelbottom=False, labelleft=False)
        
        # Vẽ đường đi của A*
        if path:
            px = [p[0] for p in path]
            py = [p[1] for p in path]
            ax.plot(px, py, color='#fbbf24', linewidth=4.5, zorder=5)
            
        # Vẽ điểm xuất phát và đích
        ax.scatter(start[0], start[1], color='#10b981', marker='o', s=180, label='Xuất phát (A)', zorder=10)
        ax.scatter(goal[0], goal[1], color='#ef4444', marker='X', s=180, label='Đích đến (B)', zorder=10)
        
        # Tô màu ký hiệu nếu có kẹt xe
        if is_jam:
            # Vẽ các dấu tam giác cảnh báo nhỏ tại vùng kẹt xe
            ax.scatter([16]*5, [6, 11, 18, 22, 27], color='#ef4444', marker='^', s=80, label='Vùng Kẹt xe (cost=5)', zorder=8)
            
        ax.set_title(title, fontsize=11, weight='bold', pad=10)
        ax.legend(loc='upper right')

    draw_scenario(ax1, grid_free, res_free["path"], f"Khung giờ Thấp điểm (00:00)\nĐường đi ngắn nhất xuyên qua trung tâm (Chi phí: {res_free['cost']:.2f})", False)
    draw_scenario(ax2, grid_jam, res_jam["path"], f"Giờ cao điểm sáng (08:00)\nA* tự động bẻ lái tránh trục kẹt xe dọc (Chi phí: {res_jam['cost']:.2f})", True)
    
    plt.suptitle("Khả năng Né tránh Kẹt xe động theo thời gian của thuật toán A*", fontsize=14, weight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "traffic_avoidance_comparison.png"), bbox_inches='tight')
    plt.close()
    print("Saved image: traffic_avoidance_comparison.png")

# --- ẢNH 3: Biểu đồ cột so sánh số lượng node đã duyệt (Heuristics) ---
def export_heuristics_performance_chart():
    print("Drawing: heuristics_nodes_expanded.png...")
    grid = get_preset_32x32()
    start = (5, 5)
    goal = (28, 8)
    
    heuristics_to_compare = ["Manhattan", "Euclidean", "Octile", "Dijkstra"]
    nodes_expanded = []
    path_costs = []
    
    for name in heuristics_to_compare:
        res = a_star_search(grid, start, goal, name)
        nodes_expanded.append(len(res["visited"]))
        path_costs.append(res["cost"])
        
    # Vẽ biểu đồ so sánh số lượng node đã duyệt
    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444']
    
    bars = ax.bar(heuristics_to_compare, nodes_expanded, color=colors, edgecolor='#1e293b', width=0.55)
    
    # Ghi số lượng nút trên đầu mỗi cột
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, yval + 15, f"{yval:,} ô", ha='center', va='bottom', fontsize=9, weight='bold')
        
    ax.set_ylabel("Số lượng ô lưới đã duyệt (Visited Nodes)", fontsize=10, weight='bold')
    ax.set_xlabel("Hàm ước lượng Heuristic h(n)", fontsize=10, weight='bold')
    ax.set_title("So sánh số ô đã duyệt của các Heuristics (Depot -> Điểm giao 4)", fontsize=12, weight='bold', pad=15)
    ax.set_ylim(0, max(nodes_expanded) * 1.15)
    
    # Bổ sung thông tin chi phí dưới mỗi cột dưới dạng bảng ghi chú
    notes_text = "Chi phí lộ trình cuối cùng:\n" + " | ".join([f"{name}: {cost:.2f}" for name, cost in zip(heuristics_to_compare, path_costs)])
    plt.figtext(0.5, -0.05, notes_text, ha="center", fontsize=9, bbox={"facecolor": "orange", "alpha": 0.1, "pad": 5}, weight='medium')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "heuristics_nodes_expanded.png"), bbox_inches='tight')
    plt.close()
    print("Saved image: heuristics_nodes_expanded.png")

# --- ẢNH 4: Lập lộ trình TSP trên bản đồ Moving AI thật (Berlin 256x256) ---
def export_berlin_256_tsp():
    print("Drawing: berlin_256_tsp.png...")
    # Thử nạp bản đồ Berlin thực tế từ dataset
    map_path = r"d:\CNTT\TRITUENHANTAO\BTL\dataset\Berlin_1_256.map"
    if not os.path.exists(map_path):
        # Nếu chưa tải bản đồ thật, thử lấy bản đồ mô phỏng trong web/public/maps
        map_path = r"d:\CNTT\TRITUENHANTAO\BTL\web\public\maps\Berlin_1_256.map"
        
    if not os.path.exists(map_path):
        print("[WARNING] Could not find Berlin_1_256.map. Skipping Berlin TSP plot.")
        return
        
    # Đọc bản đồ
    with open(map_path, 'r') as f:
        lines = f.readlines()
        
    height = 0
    width = 0
    map_start = -1
    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith("height"):
            height = int(line.split()[1])
        elif line.startswith("width"):
            width = int(line.split()[1])
        elif line.startswith("map"):
            map_start = i + 1
            break
            
    grid = np.zeros((height, width))
    for idx, i in enumerate(range(map_start, map_start + height)):
        row_text = lines[i].strip()
        for j in range(width):
            grid[idx, j] = 1 if row_text[j] in ['.', 'G'] else 0
            
    # Thiết lập Kho và Các điểm dừng (Dùng vị trí đi lại được)
    depot = (115, 225)
    stops = [(95, 55), (180, 25), (120, 110), (60, 100)]
    all_pts = [depot] + stops
    
    n = len(all_pts)
    dist_matrix = [[0]*n for _ in range(n)]
    paths = [[None]*n for _ in range(n)]
    
    for i in range(n):
        for j in range(n):
            if i != j:
                res = a_star_search(grid, all_pts[i], all_pts[j], "Octile")
                dist_matrix[i][j] = res["cost"]
                paths[i][j] = res["path"]
                
    tour, tour_cost = solve_tsp(dist_matrix)
    
    fig, ax = plt.subplots(figsize=(9, 9), dpi=150)
    
    # Vẽ chướng ngại vật màu đen, đường trống màu xám nhạt
    cmap_grid = np.zeros((height, width, 3))
    for y in range(height):
        for x in range(width):
            if grid[y, x] == 0:
                cmap_grid[y, x] = [0.15, 0.15, 0.18] # Dark charcoal
            else:
                cmap_grid[y, x] = [0.93, 0.94, 0.96] # Light road
                
    ax.imshow(cmap_grid, origin='upper')
    ax.axis('off')
    
    # Vẽ lộ trình TSP nối liền
    for k in range(len(tour) - 1):
        u, v = tour[k], tour[k+1]
        path = paths[u][v]
        if path:
            px = [p[0] for p in path]
            py = [p[1] for p in path]
            ax.plot(px, py, color='#fbbf24', linewidth=3, zorder=5)
            
    # Vẽ kho Depot
    ax.scatter(depot[0], depot[1], color='#eab308', edgecolors='#0f172a', marker='*', s=250, label='Kho Depot', zorder=10)
    # Vẽ stops
    for idx, (sx, sy) in enumerate(stops):
        ax.scatter(sx, sy, color='#9b5de5', edgecolors='white', marker='o', s=120, zorder=10)
        ax.text(sx, sy, str(idx+1), color='white', fontsize=7, weight='bold', ha='center', va='center', zorder=11)
        
    ax.set_title(f"Lộ trình tối ưu qua 4 địa chỉ trên Bản đồ Berlin thực tế (256x256)\n(Hành trình vòng khép kín giải bằng Greedy + 2-Opt | Tổng chi phí: {tour_cost:.2f})", fontsize=11, weight='bold', pad=15)
    ax.legend(loc='upper right')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "berlin_256_tsp.png"), bbox_inches='tight')
    plt.close()
    print("Saved image: berlin_256_tsp.png")

# ==========================================================================
# CHẠY TẤT CẢ CÁC TÀI NGUYÊN
# ==========================================================================
if __name__ == "__main__":
    print("=== STARTING REPORT ASSETS GENERATION ===")
    start_time = time.time()
    
    export_route_32x32_tsp()
    export_traffic_avoidance_comparison()
    export_heuristics_performance_chart()
    export_berlin_256_tsp()
    
    print(f"=== SUCCESSFULLY GENERATED IMAGES IN DIR: {output_dir} ===")
    print(f"Total processing time: {time.time() - start_time:.2f} seconds.")
