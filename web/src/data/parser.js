/**
 * Parses Moving AI .map file string content.
 * @param {string} textContent - raw text of .map file
 * @returns {{width: number, height: number, grid: Array<Array<number>>}}
 */
export function parseMovingAIMap(textContent) {
  const lines = textContent.split(/\r?\n/);
  let height = 0;
  let width = 0;
  let mapStartIdx = -1;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (line.startsWith("height")) {
      height = parseInt(line.split(/\s+/)[1], 10);
    } else if (line.startsWith("width")) {
      width = parseInt(line.split(/\s+/)[1], 10);
    } else if (line.startsWith("map")) {
      mapStartIdx = i + 1;
      break;
    }
  }

  if (mapStartIdx === -1 || height === 0 || width === 0) {
    throw new Error("Invalid .map file format");
  }

  const grid = [];
  for (let i = mapStartIdx; i < mapStartIdx + height; i++) {
    if (i < lines.length && lines[i].trim().length > 0) {
      const rowText = lines[i].trim();
      const row = [];
      
      // Parse characters:
      // . or G -> passable (weight = 1)
      // S -> swamp (weight = 5)
      // W -> water (weight = 8)
      // Others -> obstacle (weight = 0)
      for (let j = 0; j < width; j++) {
        if (j < rowText.length) {
          const char = rowText[j];
          if (char === '.' || char === 'G') {
            row.push(1); // normal road
          } else if (char === 'S') {
            row.push(5); // swamp (high cost)
          } else if (char === 'W') {
            row.push(8); // water (very high cost)
          } else {
            row.push(0); // obstacle
          }
        } else {
          row.push(0); // pad missing cells as obstacles
        }
      }
      grid.push(row);
    }
  }

  return { width, height, grid };
}
export default parseMovingAIMap;
