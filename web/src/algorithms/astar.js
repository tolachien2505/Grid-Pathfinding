// Helper Heuristics
export const Heuristics = {
  Manhattan: (p1, p2) => Math.abs(p1.x - p2.x) + Math.abs(p1.y - p2.y),
  Euclidean: (p1, p2) => Math.sqrt(Math.pow(p1.x - p2.x, 2) + Math.pow(p1.y - p2.y, 2)),
  Chebyshev: (p1, p2) => Math.max(Math.abs(p1.x - p2.x), Math.abs(p1.y - p2.y)),
  Octile: (p1, p2) => {
    const dx = Math.abs(p1.x - p2.x);
    const dy = Math.abs(p1.y - p2.y);
    return (dx + dy) + (Math.sqrt(2) - 2) * Math.min(dx, dy);
  },
  Dijkstra: () => 0
};

// Priority Queue implementation (Min-Heap) for A* efficiency
class MinHeap {
  constructor() {
    this.heap = [];
  }

  push(item) {
    this.heap.push(item);
    this.bubbleUp(this.heap.length - 1);
  }

  pop() {
    if (this.heap.length === 0) return null;
    const min = this.heap[0];
    const end = this.heap.pop();
    if (this.heap.length > 0) {
      this.heap[0] = end;
      this.sinkDown(0);
    }
    return min;
  }

  bubbleUp(n) {
    const element = this.heap[n];
    while (n > 0) {
      const parentN = Math.floor((n + 1) / 2) - 1;
      const parent = this.heap[parentN];
      if (element.priority >= parent.priority) break;
      this.heap[parentN] = element;
      this.heap[n] = parent;
      n = parentN;
    }
  }

  sinkDown(n) {
    const length = this.heap.length;
    const element = this.heap[n];
    while (true) {
      const child2N = (n + 1) * 2;
      const child1N = child2N - 1;
      let swap = null;

      if (child1N < length) {
        const child1 = this.heap[child1N];
        if (child1.priority < element.priority) swap = child1N;
      }
      if (child2N < length) {
        const child2 = this.heap[child2N];
        const compare = swap === null ? element : this.heap[swap];
        if (child2.priority < compare.priority) swap = child2N;
      }

      if (swap === null) break;
      this.heap[n] = this.heap[swap];
      this.heap[swap] = element;
      n = swap;
    }
  }

  size() {
    return this.heap.length;
  }
}

/**
 * A* Pathfinding Search
 * @param {Array<Array<number>>} grid - 2D matrix (0 for obstacles, >0 for traversable weights)
 * @param {{x: number, y: number}} start - start coordinate
 * @param {{x: number, y: number}} goal - goal coordinate
 * @param {string} heuristicName - Manhattan, Euclidean, Chebyshev, Octile, Dijkstra
 * @returns {{path: Array<{x: number, y: number}>, cost: number, visitedNodesInOrder: Array<{x: number, y: number}>, elapsedMs: number}}
 */
export function aStarSearch(grid, start, goal, heuristicName = "Octile") {
  const tStart = performance.now();
  const height = grid.length;
  const width = grid[0].length;
  const heuristicFunc = Heuristics[heuristicName] || Heuristics.Octile;

  const pq = new MinHeap();
  pq.push({ x: start.x, y: start.y, priority: heuristicFunc(start, goal) });

  const cameFrom = {};
  const gScore = {};
  const startKey = `${start.x},${start.y}`;
  gScore[startKey] = 0;

  const visitedNodesInOrder = [];
  const visitedSet = new Set();
  const expandedSet = new Set();

  // Directions: 8-way movement
  const directions = [
    { dx: 1, dy: 0, weight: 1.0 },
    { dx: -1, dy: 0, weight: 1.0 },
    { dx: 0, dy: 1, weight: 1.0 },
    { dx: 0, dy: -1, weight: 1.0 },
    { dx: 1, dy: 1, weight: Math.SQRT2 },
    { dx: -1, dy: 1, weight: Math.SQRT2 },
    { dx: 1, dy: -1, weight: Math.SQRT2 },
    { dx: -1, dy: -1, weight: Math.SQRT2 }
  ];

  let found = false;

  while (pq.size() > 0) {
    const current = pq.pop();
    const currentKey = `${current.x},${current.y}`;

    if (current.x === goal.x && current.y === goal.y) {
      found = true;
      break;
    }

    if (expandedSet.has(currentKey)) continue;
    expandedSet.add(currentKey);
    
    // Track visited nodes in order of expansion (excluding start and goal for clean display)
    if (currentKey !== startKey) {
      visitedNodesInOrder.push({ x: current.x, y: current.y });
    }

    for (const dir of directions) {
      const nx = current.x + dir.dx;
      const ny = current.y + dir.dy;

      // Bound checking
      if (nx >= 0 && nx < width && ny >= 0 && ny < height) {
        const cellCost = grid[ny][nx]; // cost/weight of cell. 0 represents obstacle.
        
        if (cellCost > 0) { // Check if passable
          const neighborKey = `${nx},${ny}`;
          const transitionCost = dir.weight * cellCost;
          const tentativeGScore = gScore[currentKey] + transitionCost;

          if (gScore[neighborKey] === undefined || tentativeGScore < gScore[neighborKey]) {
            cameFrom[neighborKey] = { x: current.x, y: current.y };
            gScore[neighborKey] = tentativeGScore;
            
            const f = tentativeGScore + heuristicFunc({ x: nx, y: ny }, goal);
            pq.push({ x: nx, y: ny, priority: f });
          }
        }
      }
    }
  }

  const tEnd = performance.now();
  const elapsedMs = tEnd - tStart;

  if (found) {
    const path = [];
    let curr = goal;
    const goalKey = `${goal.x},${goal.y}`;
    path.push(curr);

    while (curr.x !== start.x || curr.y !== start.y) {
      const currKey = `${curr.x},${curr.y}`;
      curr = cameFrom[currKey];
      path.push(curr);
    }
    path.reverse();

    return {
      path,
      cost: gScore[goalKey],
      visitedNodesInOrder,
      elapsedMs
    };
  }

  return {
    path: [],
    cost: Infinity,
    visitedNodesInOrder,
    elapsedMs
  };
}
export default aStarSearch;
