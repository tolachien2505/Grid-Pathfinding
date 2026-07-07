// Default 32x32 Grid Map preset
export const default32x32Grid = Array(32).fill(null).map((_, y) => {
  return Array(32).fill(null).map((_, x) => {
    // Generate a default map with some obstacles
    // Outer walls
    if (x === 0 || x === 31 || y === 0 || y === 31) return 0; // 0 represents obstacle
    
    // Add some random buildings/blocks
    if (y === 8 && x >= 5 && x <= 15) return 0;
    if (y === 8 && x >= 18 && x <= 26) return 0;
    
    if (y === 16 && x >= 5 && x <= 12) return 0;
    if (y === 16 && x >= 15 && x <= 27) return 0;
    
    if (y === 24 && x >= 8 && x <= 22) return 0;
    
    // Some vertical dividers to create streets
    if (x === 14 && y >= 3 && y <= 6) return 0;
    if (x === 14 && y >= 10 && y <= 14) return 0;
    if (x === 17 && y >= 18 && y <= 22) return 0;
    if (x === 7 && y >= 18 && y <= 29) return 0;
    if (x === 24 && y >= 2 && y <= 12) return 0;

    return 1; // 1 represents clear road/pathway
  });
});

export const PRESET_MAPS = [
  {
    id: "custom_32",
    name: "Lưới tự vẽ (32x32)",
    width: 32,
    height: 32,
    type: "local",
    data: default32x32Grid
  },
  {
    id: "berlin_256",
    name: "Berlin (256x256) - Moving AI",
    width: 256,
    height: 256,
    type: "fetch",
    path: "/maps/Berlin_1_256.map"
  },
  {
    id: "boston_256",
    name: "Boston (256x256) - Moving AI",
    width: 256,
    height: 256,
    type: "fetch",
    path: "/maps/Boston_0_256.map"
  }
];

export default PRESET_MAPS;
