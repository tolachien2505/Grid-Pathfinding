import { aStarSearch } from './astar';

/**
 * Calculates a full Distance Matrix for depot + delivery points using A* Search.
 * @param {Array<Array<number>>} grid - 2D grid matrix
 * @param {Array<{x: number, y: number}>} points - list of points, where index 0 is Depot
 * @param {string} heuristicName - Manhattan, Euclidean, Chebyshev, Octile, Dijkstra
 * @returns {{distMatrix: Array<Array<number>>, pathMatrix: Array<Array<Array<{x: number, y: number}>>>}}
 */
export function computeDistanceMatrix(grid, points, heuristicName = "Octile") {
  const n = points.length;
  const distMatrix = Array(n).fill(null).map(() => Array(n).fill(0));
  const pathMatrix = Array(n).fill(null).map(() => Array(n).fill(null));

  for (let i = 0; i < n; i++) {
    for (let j = 0; j < n; j++) {
      if (i === j) {
        distMatrix[i][j] = 0;
      } else {
        const result = aStarSearch(grid, points[i], points[j], heuristicName);
        distMatrix[i][j] = result.cost;
        pathMatrix[i][j] = result.path;
      }
    }
  }

  return { distMatrix, pathMatrix };
}

/**
 * Solve TSP using Nearest Neighbor + 2-Opt local search refinement.
 * @param {Array<Array<number>>} distMatrix - pairwise distance matrix
 * @returns {{tour: Array<number>, cost: number}}
 */
export function solveTSP(distMatrix) {
  const n = distMatrix.length;
  if (n === 0) return { tour: [], cost: 0 };
  if (n === 1) return { tour: [0, 0], cost: 0 };
  if (n === 2) return { tour: [0, 1, 0], cost: distMatrix[0][1] + distMatrix[1][0] };

  // 1. Initial Tour using Greedy Nearest Neighbor
  const unvisited = new Set(Array.from({ length: n - 1 }, (_, i) => i + 1)); // 1 to n-1
  let tour = [0];
  let current = 0;

  while (unvisited.size > 0) {
    let nextNode = -1;
    let minDist = Infinity;
    
    for (const node of unvisited) {
      if (distMatrix[current][node] < minDist) {
        minDist = distMatrix[current][node];
        nextNode = node;
      }
    }

    tour.push(nextNode);
    unvisited.delete(nextNode);
    current = nextNode;
  }
  tour.push(0); // Return to depot

  const getTourCost = (t) => {
    let sum = 0;
    for (let i = 0; i < t.length - 1; i++) {
      sum += distMatrix[t[i]][t[i + 1]];
    }
    return sum;
  };

  let bestTour = [...tour];
  let bestCost = getTourCost(bestTour);

  // 2. 2-Opt Swap Local Search
  let improved = true;
  let iterations = 0;
  const maxIterations = 1000;

  while (improved && iterations < maxIterations) {
    improved = false;
    iterations++;

    for (let i = 1; i < bestTour.length - 2; i++) {
      for (let j = i + 1; j < bestTour.length - 1; j++) {
        // Reverse sub-array bestTour[i...j]
        const newTour = [...bestTour];
        const subTour = newTour.slice(i, j + 1).reverse();
        newTour.splice(i, subTour.length, ...subTour);
        
        const newCost = getTourCost(newTour);

        if (newCost < bestCost - 0.0001) {
          bestTour = newTour;
          bestCost = newCost;
          improved = true;
          break;
        }
      }
      if (improved) break;
    }
  }

  return { tour: bestTour, cost: bestCost };
}
