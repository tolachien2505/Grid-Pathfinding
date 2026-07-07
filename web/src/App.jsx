import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, 
  RotateCcw, 
  MapPin, 
  Home, 
  Flame, 
  Grid, 
  Sliders, 
  BarChart2, 
  Clock, 
  Upload, 
  Info,
  CheckCircle,
  AlertTriangle
} from 'lucide-react';
import { PRESET_MAPS } from './data/presets';
import { parseMovingAIMap } from './data/parser';
import { aStarSearch, Heuristics } from './algorithms/astar';
import { solveTSP, computeDistanceMatrix } from './algorithms/tsp';

function App() {
  // Lựa chọn bản đồ (Preset)
  const [selectedPresetId, setSelectedPresetId] = useState("custom_32");
  const [grid, setGrid] = useState([]);
  const [gridWidth, setGridWidth] = useState(32);
  const [gridHeight, setGridHeight] = useState(32);
  const [mapLoading, setMapLoading] = useState(false);
  
  // Các điểm tương tác (Kho Depot và các Điểm giao hàng)
  const [depot, setDepot] = useState({ x: 5, y: 5 });
  const [deliveries, setDeliveries] = useState([
    { x: 10, y: 22 },
    { x: 25, y: 12 },
    { x: 18, y: 25 },
    { x: 28, y: 8 }
  ]);

  // Cấu hình kẹt xe theo khung giờ (0 đến 23)
  const [trafficHour, setTrafficHour] = useState(8); // 8:00 sáng
  
  // Các thông số thuật toán
  const [selectedHeuristic, setSelectedHeuristic] = useState("Octile");
  const [paintMode, setPaintMode] = useState("obstacle"); // obstacle, traffic, depot, delivery, clear
  const [animationSpeed, setAnimationSpeed] = useState(50); // Tốc độ chạy A* (ms)

  // Trạng thái bộ giải (Solver States)
  const [isSolving, setIsSolving] = useState(false);
  const [tourIndices, setTourIndices] = useState([]);
  const [tourCost, setTourCost] = useState(0);
  const [optimalPaths, setOptimalPaths] = useState(null); // Đường đi A* giữa từng cặp điểm
  
  // Trạng thái hoạt họa A* và so sánh Heuristics
  const [animatedVisited, setAnimatedVisited] = useState([]);
  const [animatingIndex, setAnimatingIndex] = useState(-1);
  const [comparisonStats, setComparisonStats] = useState([]);
  
  // Trạng thái tối ưu hóa hiệu năng giảm lag
  const [autoSolveEnabled, setAutoSolveEnabled] = useState(true);
  const [presetLoadedPendingSolve, setPresetLoadedPendingSolve] = useState(true);

  const canvasRef = useRef(null);
  const fileInputRef = useRef(null);
  const isDrawingRef = useRef(false);
  const offscreenCanvasRef = useRef(null);

  // Kích thước Canvas cố định
  const canvasSize = 512;

  // Tải bản đồ khi đổi Preset
  useEffect(() => {
    const preset = PRESET_MAPS.find(m => m.id === selectedPresetId);
    if (!preset) return;

    // Reset lại cờ chờ giải để đường chạy mẫu vẽ ra ngay khi tải bản đồ xong
    setPresetLoadedPendingSolve(true);

    if (preset.type === "local") {
      setGridWidth(preset.width);
      setGridHeight(preset.height);
      setGrid(JSON.parse(JSON.stringify(preset.data)));
      setAutoSolveEnabled(true); // Lưới nhỏ bật sẵn tự động tính toán
      
      // Khởi tạo lại vị trí Depot & Điểm giao phù hợp lưới 32x32
      setDepot({ x: 5, y: 5 });
      setDeliveries([
        { x: 10, y: 22 },
        { x: 25, y: 12 },
        { x: 18, y: 25 },
        { x: 28, y: 8 }
      ]);
      resetSolverStates();
    } else if (preset.type === "fetch") {
      setMapLoading(true);
      resetSolverStates();
      setAutoSolveEnabled(false); // Bản đồ lớn tắt tự động chạy để tránh lag
      fetch(preset.path)
        .then(res => {
          if (!res.ok) throw new Error("Could not fetch map");
          return res.text();
        })
        .then(text => {
          const parsed = parseMovingAIMap(text);
          setGridWidth(parsed.width);
          setGridHeight(parsed.height);
          setGrid(parsed.grid);
          
          // Tìm các vị trí đi lại được để đặt Kho và Điểm giao ngẫu nhiên
          const passable = [];
          for (let y = 30; y < parsed.height - 30; y += 15) {
            for (let x = 30; x < parsed.width - 30; x += 15) {
              if (parsed.grid[y] && parsed.grid[y][x] === 1) {
                passable.push({ x, y });
              }
            }
          }
          
          if (passable.length > 5) {
            setDepot(passable[0]);
            setDeliveries(passable.slice(1, 5)); // Đặt mặc định 4 điểm giao hàng
          }
          setMapLoading(false);
        })
        .catch(err => {
          console.error(err);
          alert("Không thể tải bản đồ. Đang quay lại lưới tự vẽ.");
          setSelectedPresetId("custom_32");
          setMapLoading(false);
        });
    }
  }, [selectedPresetId]);

  // Reset các kết quả tính toán trước đó
  const resetSolverStates = () => {
    setTourIndices([]);
    setTourCost(0);
    setOptimalPaths(null);
    setAnimatedVisited([]);
    setAnimatingIndex(-1);
  };

  // Tự động tính toán lại lộ trình nếu bật Auto-Solve hoặc có yêu cầu chạy mẫu lần đầu tiên
  useEffect(() => {
    if (grid.length > 0 && !isSolving && (autoSolveEnabled || presetLoadedPendingSolve)) {
      autoSolveRoute();
      if (presetLoadedPendingSolve) {
        setPresetLoadedPendingSolve(false);
      }
    }
  }, [grid, trafficHour, depot, deliveries, selectedHeuristic, autoSolveEnabled, presetLoadedPendingSolve]);

  // Tạo lưới trọng số động kết hợp mô phỏng kẹt xe theo giờ
  const getDynamicGrid = () => {
    const height = grid.length;
    if (height === 0) return [];
    const width = grid[0].length;
    
    const dynamicGrid = Array(height).fill(null).map(() => Array(width).fill(1));
    
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        const baseCost = grid[y][x];
        if (baseCost === 0) {
          dynamicGrid[y][x] = 0; // Vật cản
          continue;
        }
        
        let multiplier = 1.0;
        
        // Mô phỏng kẹt xe theo khung giờ trên các trục đường chính
        if (trafficHour >= 7 && trafficHour <= 9) {
          // Giờ cao điểm sáng kẹt các trục lộ trung tâm
          if (Math.abs(y - height / 2) < height * 0.03 || Math.abs(x - width / 2) < width * 0.03) {
            multiplier = 5.0; 
          } else if (Math.abs(y - height / 4) < height * 0.02 || Math.abs(x - width / 4) < width * 0.02) {
            multiplier = 3.0;
          }
        } else if (trafficHour >= 11 && trafficHour <= 13) {
          // Giờ trưa kẹt khu vực trung tâm đô thị (CBD)
          const dx = x - width / 2;
          const dy = y - height / 2;
          const dist = Math.sqrt(dx*dx + dy*dy);
          const maxRadius = Math.min(width, height) * 0.18;
          if (dist < maxRadius) {
            multiplier = 5.0 - (dist / maxRadius) * 4.0;
          }
        } else if (trafficHour >= 17 && trafficHour <= 19) {
          // Giờ cao điểm chiều kẹt diện rộng
          const dx = x - width / 2;
          const dy = y - height / 2;
          const dist = Math.sqrt(dx*dx + dy*dy);
          const maxRadius = Math.min(width, height) * 0.35;
          if (dist < maxRadius) {
            multiplier = 4.0;
          }
        }
        
        dynamicGrid[y][x] = baseCost * multiplier;
      }
    }
    return dynamicGrid;
  };

  // Lập lộ trình tối ưu qua toàn bộ các điểm giao hàng
  const autoSolveRoute = () => {
    if (grid.length === 0) return;
    const dynamicGrid = getDynamicGrid();
    const allPoints = [depot, ...deliveries];
    
    // Kiểm tra xem có điểm nào đặt đè lên chướng ngại vật hay không
    for (const pt of allPoints) {
      if (grid[pt.y] && grid[pt.y][pt.x] === 0) return;
    }

    try {
      // 1. Tính toán ma trận khoảng cách giữa mọi cặp điểm dừng bằng A*
      const { distMatrix, pathMatrix } = computeDistanceMatrix(dynamicGrid, allPoints, selectedHeuristic);
      
      // Kiểm tra tính liên thông của bản đồ
      let fullyConnected = true;
      for (let i = 0; i < allPoints.length; i++) {
        for (let j = 0; j < allPoints.length; j++) {
          if (i !== j && distMatrix[i][j] === Infinity) {
            fullyConnected = false;
            break;
          }
        }
      }
      
      if (!fullyConnected) {
        setTourIndices([]);
        setTourCost(0);
        setOptimalPaths(null);
        return;
      }

      // 2. Tìm thứ tự đi tối ưu qua chuỗi điểm bằng bộ giải TSP
      const { tour, cost } = solveTSP(distMatrix);
      setTourIndices(tour);
      setTourCost(cost);
      setOptimalPaths(pathMatrix);
    } catch (e) {
      console.error(e);
    }
  };

  // Chạy giả lập hoạt họa sóng tìm kiếm A* (Từ Kho -> Điểm Giao 1)
  const animateAStar = () => {
    if (grid.length === 0 || deliveries.length === 0) return;
    setIsSolving(true);
    resetSolverStates();
    
    const dynamicGrid = getDynamicGrid();
    const result = aStarSearch(dynamicGrid, depot, deliveries[0], selectedHeuristic);
    
    if (result.path.length === 0) {
      alert("Không tìm thấy đường đi giữa Depot và Điểm giao hàng 1!");
      setIsSolving(false);
      return;
    }

    setAnimatedVisited(result.visitedNodesInOrder);
    setAnimatingIndex(0);
  };

  // Điều khiển tiến trình của hiệu ứng lan truyền A*
  useEffect(() => {
    if (animatingIndex >= 0 && animatingIndex < animatedVisited.length) {
      // Tăng số ô vẽ mỗi khung hình để chạy mượt mà trên bản đồ lớn
      const increment = gridWidth > 32 ? Math.max(12, Math.floor(gridWidth / 2)) : 1;
      const timer = setTimeout(() => {
        setAnimatingIndex(prev => Math.min(prev + increment, animatedVisited.length));
      }, animationSpeed / 10);
      return () => clearTimeout(timer);
    } else if (animatingIndex >= animatedVisited.length && isSolving) {
      setIsSolving(false);
      autoSolveRoute();
    }
  }, [animatingIndex, animatedVisited, isSolving]);

  // Nhấn nút So sánh Heuristics chạy ngầm Manhattan, Euclidean và Octile
  const runComparison = () => {
    if (grid.length === 0 || deliveries.length === 0) return;
    const dynamicGrid = getDynamicGrid();
    const startPt = depot;
    const endPt = deliveries[0];
    
    const targets = ["Manhattan", "Euclidean", "Octile"];
    const stats = targets.map(name => {
      const result = aStarSearch(dynamicGrid, startPt, endPt, name);
      return {
        name,
        cost: result.path.length > 0 ? result.cost : Infinity,
        expanded: result.visitedNodesInOrder.length,
        time: result.elapsedMs
      };
    });

    setComparisonStats(stats);
  };

  // 1. Vẽ bản đồ tĩnh lên Offscreen Canvas khi bản đồ hoặc giờ kẹt xe thay đổi (Chỉ vẽ 1 lần khi có thay đổi)
  useEffect(() => {
    if (grid.length === 0) return;
    
    // Khởi tạo Canvas ẩn nếu chưa tồn tại
    if (!offscreenCanvasRef.current) {
      offscreenCanvasRef.current = document.createElement('canvas');
    }
    const offscreen = offscreenCanvasRef.current;
    offscreen.width = canvasSize;
    offscreen.height = canvasSize;
    const ctx = offscreen.getContext('2d');
    
    const cellWidth = canvasSize / gridWidth;
    const cellHeight = canvasSize / gridHeight;
    const dynamicGrid = getDynamicGrid();
    
    ctx.clearRect(0, 0, canvasSize, canvasSize);
    
    // Vẽ nền đường và các ô chướng ngại vật
    for (let y = 0; y < gridHeight; y++) {
      for (let x = 0; x < gridWidth; x++) {
        const baseCost = grid[y][x];
        const dynamicCost = dynamicGrid[y][x];
        
        if (baseCost === 0) {
          // Ô Vật cản (Tường xám đậm với họa tiết chéo tòa nhà)
          ctx.fillStyle = '#334155';
          ctx.fillRect(x * cellWidth, y * cellHeight, cellWidth, cellHeight);
          
          // Vẽ họa tiết sọc chéo giả lập tòa nhà
          ctx.strokeStyle = '#475569';
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(x * cellWidth, y * cellHeight);
          ctx.lineTo((x + 1) * cellWidth, (y + 1) * cellHeight);
          ctx.stroke();
        } else {
          // Ô Đường đi bình thường (Màu xám mặt đường nhạt, màu cam/đỏ kẹt xe)
          if (dynamicCost === 1.0) {
            ctx.fillStyle = '#f1f5f9';
          } else if (dynamicCost < 3.0) {
            ctx.fillStyle = '#e2e8f0';
          } else if (dynamicCost < 5.0) {
            ctx.fillStyle = '#ffedd5'; // Tắc vừa
          } else {
            ctx.fillStyle = '#fee2e2'; // Tắc nặng
          }
          
          // Vẽ địa hình đặc biệt
          if (baseCost === 5) {
            ctx.fillStyle = '#d9f99d'; // Đầm lầy
          } else if (baseCost === 8) {
            ctx.fillStyle = '#bae6fd'; // Sông nước
          }
          
          ctx.fillRect(x * cellWidth, y * cellHeight, cellWidth, cellHeight);
          
          // Vẽ ký hiệu cảnh báo kẹt xe (⚠)
          if (dynamicCost >= 3.0) {
            ctx.fillStyle = dynamicCost >= 5.0 ? '#ef4444' : '#f97316';
            ctx.font = `bold ${Math.max(9, cellHeight * 0.6)}px sans-serif`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText('⚠', x * cellWidth + cellWidth / 2, y * cellHeight + cellHeight / 2);
          }
        }
        
        // Vẽ đường lưới mờ cho bản đồ lưới tự vẽ 32x32
        if (gridWidth <= 32) {
          ctx.strokeStyle = '#cbd5e1';
          ctx.lineWidth = 0.5;
          ctx.strokeRect(x * cellWidth, y * cellHeight, cellWidth, cellHeight);
        }
      }
    }
  }, [grid, gridWidth, gridHeight, trafficHour]);

  // 2. Vẽ hoạt ảnh chuyển động của lộ trình và sóng tìm kiếm A* lên Canvas chính ở tốc độ 60fps
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || grid.length === 0) return;
    const ctx = canvas.getContext('2d');
    
    const cellWidth = canvasSize / gridWidth;
    const cellHeight = canvasSize / gridHeight;
    
    let animationFrameId;
    let lineDashOffset = 0;

    const draw = () => {
      ctx.clearRect(0, 0, canvasSize, canvasSize);
      
      // Vẽ ảnh nền tĩnh đã render sẵn từ Offscreen Canvas - SIÊU NHANH (<0.05ms)
      if (offscreenCanvasRef.current) {
        ctx.drawImage(offscreenCanvasRef.current, 0, 0);
      }
      
      // Vẽ vùng lan truyền thuật toán A* nếu đang chạy giả lập
      if (animatingIndex >= 0) {
        ctx.fillStyle = 'rgba(0, 210, 255, 0.35)';
        for (let i = 0; i < animatingIndex; i++) {
          const pt = animatedVisited[i];
          if (pt) {
            ctx.fillRect(pt.x * cellWidth, pt.y * cellHeight, cellWidth, cellHeight);
          }
        }
      }

      // Vẽ Lộ trình cuối cùng (Đường nối đậm nét đứt chuyển động đè lên trên)
      if (animatingIndex === -1 && tourIndices.length > 0 && optimalPaths) {
        ctx.strokeStyle = '#fbbf24'; // Màu vàng Neon phản quang rực rỡ
        ctx.lineWidth = 5.5; 
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        
        // Hiệu ứng phát sáng
        ctx.shadowColor = 'rgba(251, 191, 36, 0.7)';
        ctx.shadowBlur = 10;
        
        ctx.setLineDash([12, 10]);
        ctx.lineDashOffset = -lineDashOffset;
        
        ctx.beginPath();
        
        for (let i = 0; i < tourIndices.length - 1; i++) {
          const u = tourIndices[i];
          const v = tourIndices[i+1];
          const path = optimalPaths[u][v];
          
          if (path && path.length > 0) {
            path.forEach((pt, idx) => {
              const cx = pt.x * cellWidth + cellWidth / 2;
              const cy = pt.y * cellHeight + cellHeight / 2;
              if (idx === 0 && i === 0) {
                ctx.moveTo(cx, cy);
              } else {
                ctx.lineTo(cx, cy);
              }
            });
          }
        }
        
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.shadowBlur = 0;
      }
    };

    // Vòng lặp vẽ liên tục 60fps mượt mà
    const tick = () => {
      lineDashOffset = (lineDashOffset + 0.35) % 22;
      draw();
      animationFrameId = requestAnimationFrame(tick);
    };

    tick();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };

  }, [grid, gridWidth, gridHeight, animatingIndex, tourIndices, optimalPaths]);

  // Xử lý tương tác vẽ bằng chuột trên lưới
  const getMouseCoords = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    
    const clientX = e.clientX || (e.touches && e.touches[0].clientX);
    const clientY = e.clientY || (e.touches && e.touches[0].clientY);
    
    const x = Math.floor(((clientX - rect.left) * scaleX) / (canvas.width / gridWidth));
    const y = Math.floor(((clientY - rect.top) * scaleY) / (canvas.height / gridHeight));
    
    return { x, y };
  };

  const handleMouseDown = (e) => {
    if (isSolving || mapLoading) return;
    isDrawingRef.current = true;
    handlePaint(e);
  };

  const handleMouseMove = (e) => {
    if (!isDrawingRef.current || isSolving || mapLoading) return;
    handlePaint(e);
  };

  const handleMouseUpOrLeave = () => {
    isDrawingRef.current = false;
  };

  const handlePaint = (e) => {
    const { x, y } = getMouseCoords(e);
    if (x < 0 || x >= gridWidth || y < 0 || y >= gridHeight) return;

    if (paintMode === "depot") {
      if (grid[y][x] > 0) { // Đặt Kho tại các ô đi qua được
        setDepot({ x, y });
        resetSolverStates();
        setPaintMode("obstacle"); // Vẽ lại bình thường sau khi đặt
      }
    } else if (paintMode === "delivery") {
      if (grid[y][x] > 0) {
        const exists = deliveries.some(d => d.x === x && d.y === y);
        if (!exists && (depot.x !== x || depot.y !== y)) {
          setDeliveries(prev => [...prev, { x, y }]);
          resetSolverStates();
        }
        setPaintMode("obstacle");
      }
    } else {
      const newGrid = [...grid];
      let val = 1;
      if (paintMode === "obstacle") val = 0;
      else if (paintMode === "traffic") val = 5; // Cản trở giao thông cost=5
      else if (paintMode === "clear") val = 1;
      
      const isPointSpecial = (depot.x === x && depot.y === y) || deliveries.some(d => d.x === x && d.y === y);
      if (!isPointSpecial) {
        newGrid[y][x] = val;
        setGrid(newGrid);
        resetSolverStates();
      }
    }
  };

  // Nhập bản đồ Moving AI bên ngoài
  const handleMapUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (evt) => {
      try {
        const text = evt.target.result;
        const parsed = parseMovingAIMap(text);
        
        setSelectedPresetId("custom_uploaded");
        setGridWidth(parsed.width);
        setGridHeight(parsed.height);
        setGrid(parsed.grid);
        
        const passable = [];
        for (let y = 10; y < parsed.height - 10; y += 10) {
          for (let x = 10; x < parsed.width - 10; x += 10) {
            if (parsed.grid[y] && parsed.grid[y][x] === 1) {
              passable.push({ x, y });
            }
          }
        }
        
        if (passable.length > 5) {
          setDepot(passable[0]);
          setDeliveries(passable.slice(1, 5));
        } else {
          setDepot({ x: 0, y: 0 });
          setDeliveries([]);
        }
        resetSolverStates();
      } catch (err) {
        alert("Lỗi khi tải file bản đồ. Vui lòng kiểm tra định dạng .map.");
      }
    };
    reader.readAsText(file);
  };

  const handleClearAllStops = () => {
    setDeliveries([]);
    resetSolverStates();
  };

  const getTrafficStatusText = () => {
    if (trafficHour >= 7 && trafficHour <= 9) return "Giờ cao điểm sáng: Trục lộ kẹt xe (x5 chi phí)";
    if (trafficHour >= 11 && trafficHour <= 13) return "Giờ ăn trưa: Kẹt cục bộ quanh trung tâm (x5 chi phí)";
    if (trafficHour >= 17 && trafficHour <= 19) return "Giờ cao điểm chiều: Tắc nghẽn diện rộng (x4 chi phí)";
    return "Giờ thấp điểm: Giao thông thông thoáng (x1 chi phí)";
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="header">
        <div className="header-title-group">
          <Sliders size={28} className="header-icon" />
          <div>
            <h1>TỐI ƯU HÓA TUYẾN ĐƯỜNG GIAO HÀNG</h1>
            <p>Hệ thống tìm đường thông minh bằng A* và tối ưu chuỗi điểm giao hàng (TSP)</p>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <div className="file-upload-btn btn btn-secondary" style={{ padding: '0.5rem 1rem', fontSize: '0.8rem' }}>
            <Upload size={16} /> Import .map
            <input 
              type="file" 
              accept=".map" 
              className="file-upload-input" 
              onChange={handleMapUpload} 
              ref={fileInputRef} 
            />
          </div>
          <button 
            className="btn btn-danger" 
            style={{ padding: '0.5rem 1rem', fontSize: '0.8rem' }}
            onClick={() => {
              if (selectedPresetId === "custom_32") {
                const cleared = Array(32).fill(null).map(() => Array(32).fill(1));
                setGrid(cleared);
                resetSolverStates();
              } else {
                alert("Vui lòng chuyển sang bản đồ 'Lưới tự vẽ (32x32)' để xóa.");
              }
            }}
          >
            <RotateCcw size={16} /> Xóa lưới
          </button>
        </div>
      </header>

      {/* Grid điều khiển */}
      <main className="dashboard-grid">
        
        {/* Bảng cấu hình hệ thống */}
        <section className="glass-panel control-group">
          <h2 className="panel-title"><Sliders size={18} /> CẤU HÌNH HỆ THỐNG</h2>
          
          {/* Chọn bản đồ */}
          <div className="form-field">
            <label className="form-label">Chọn Bản đồ (Dataset)</label>
            <select 
              value={selectedPresetId} 
              onChange={(e) => setSelectedPresetId(e.target.value)}
              disabled={isSolving}
            >
              {PRESET_MAPS.map(m => (
                <option key={m.id} value={m.id}>{m.name}</option>
              ))}
              {selectedPresetId === "custom_uploaded" && (
                <option value="custom_uploaded">Tệp tin vừa import (.map)</option>
              )}
            </select>
          </div>

          {/* Chọn Heuristics */}
          <div className="form-field">
            <label className="form-label">Hàm Heuristic h(n)</label>
            <select 
              value={selectedHeuristic} 
              onChange={(e) => {
                setSelectedHeuristic(e.target.value);
                resetSolverStates();
              }}
              disabled={isSolving}
            >
              <option value="Manhattan">Manhattan Distance (4 hướng)</option>
              <option value="Euclidean">Euclidean Distance (Đường chim bay)</option>
              <option value="Chebyshev">Chebyshev Distance (8 hướng)</option>
              <option value="Octile">Octile Distance (8 hướng chéo - Khuyên dùng)</option>
              <option value="Dijkstra">Dijkstra (Null Heuristic h=0)</option>
            </select>
          </div>

          {/* Hộp kiểm Auto-solve điều khiển hiệu năng */}
          <div className="form-field" style={{ flexDirection: 'row', alignItems: 'center', gap: '0.5rem', marginTop: '-0.25rem', marginBottom: '0.5rem' }}>
            <input 
              type="checkbox" 
              id="auto-solve-chk"
              checked={autoSolveEnabled}
              onChange={(e) => setAutoSolveEnabled(e.target.checked)}
              style={{ width: '16px', height: '16px', cursor: 'pointer' }}
            />
            <label htmlFor="auto-solve-chk" style={{ fontSize: '0.85rem', cursor: 'pointer', color: 'var(--text-secondary)' }}>
              Tự động tính lộ trình (Auto-Solve)
            </label>
          </div>

          {/* Thiết lập giờ cao điểm */}
          <div className="form-field">
            <div className="hour-display">
              <span className="form-label">Khung giờ giao thông</span>
              <span className="hour-badge">{trafficHour.toString().padStart(2, '0')}:00</span>
            </div>
            <input 
              type="range" 
              min="0" 
              max="23" 
              value={trafficHour} 
              onChange={(e) => {
                setTrafficHour(parseInt(e.target.value, 10));
                resetSolverStates();
              }}
              disabled={isSolving}
            />
            <div className="traffic-status-text">
              <Clock size={12} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle' }} />
              {getTrafficStatusText()}
            </div>
          </div>

          {/* Chế độ cọ vẽ chuột */}
          <div className="form-field">
            <label className="form-label">Công cụ vẽ bản đồ</label>
            <div className="segmented-control">
              <div 
                className={`segmented-option ${paintMode === "obstacle" ? "active" : ""}`}
                onClick={() => setPaintMode("obstacle")}
                title="Vẽ chướng ngại vật"
              >
                Tường (@)
              </div>
              <div 
                className={`segmented-option ${paintMode === "traffic" ? "active" : ""}`}
                onClick={() => setPaintMode("traffic")}
                title="Vẽ vùng đường tắc hoặc đầm lầy"
              >
                Ùn tắc (S)
              </div>
              <div 
                className={`segmented-option ${paintMode === "depot" ? "active" : ""}`}
                onClick={() => setPaintMode("depot")}
                title="Đặt kho xuất phát"
              >
                Kho (D)
              </div>
              <div 
                className={`segmented-option ${paintMode === "delivery" ? "active" : ""}`}
                onClick={() => setPaintMode("delivery")}
                title="Đặt điểm cần giao hàng"
              >
                Đơn (P)
              </div>
              <div 
                className={`segmented-option ${paintMode === "clear" ? "active" : ""}`}
                onClick={() => setPaintMode("clear")}
                title="Xóa ô vật cản"
              >
                Xóa ô
              </div>
            </div>
          </div>

          {/* Chú thích màu sắc */}
          <div className="form-field">
            <span className="form-label">Chú thích bản đồ</span>
            <div className="legend-grid">
              <div className="legend-item"><div className="legend-color" style={{background: '#334155'}}/> Tường chắn (@)</div>
              <div className="legend-item"><div className="legend-color" style={{background: '#f1f5f9'}}/> Đường đi trống</div>
              <div className="legend-item"><div className="legend-color" style={{background: '#ffd700'}}/> Kho Depot (D)</div>
              <div className="legend-item"><div className="legend-color" style={{background: '#9b5de5'}}/> Điểm giao (P)</div>
              <div className="legend-item"><div className="legend-color" style={{background: '#d9f99d'}}/> Đầm lầy cost=5</div>
              <div className="legend-item"><div className="legend-color" style={{background: '#ffedd5'}}/> Tắc vừa (cost=3)</div>
              <div className="legend-item"><div className="legend-color" style={{background: '#fee2e2'}}/> Tắc nặng (cost=5)</div>
            </div>
          </div>

          {/* Nút hành động */}
          <div className="control-group" style={{ marginTop: '0.5rem' }}>
            {!autoSolveEnabled && (
              <button 
                className="btn" 
                onClick={autoSolveRoute}
                style={{ 
                  background: 'linear-gradient(135deg, var(--secondary) 0%, var(--primary) 100%)',
                  color: '#ffffff',
                  fontWeight: '700',
                  boxShadow: '0 4px 12px rgba(155, 93, 229, 0.3)'
                }}
                disabled={isSolving || mapLoading || deliveries.length === 0}
              >
                <Play size={18} /> Giải tuyến tối ưu (TSP)
              </button>
            )}
            <button 
              className="btn btn-primary" 
              onClick={animateAStar}
              disabled={isSolving || mapLoading || deliveries.length === 0}
            >
              <Play size={18} /> Chạy giả lập A* (Điểm 1)
            </button>
            <div className="button-row">
              <button 
                className="btn btn-secondary" 
                onClick={runComparison}
                disabled={isSolving || mapLoading || deliveries.length === 0}
              >
                <BarChart2 size={16} /> So sánh Heuristic
              </button>
              <button 
                className="btn btn-danger" 
                onClick={handleClearAllStops}
                disabled={isSolving || mapLoading}
              >
                Xóa các điểm giao
              </button>
            </div>
          </div>

          <div className="instructions-overlay">
            <Info size={14} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle', color: 'var(--secondary)' }} />
            Cách sử dụng: Rê chuột vẽ chướng ngại vật/ùn tắc. Chọn <strong>Kho (D)</strong> để đặt kho trung tâm, <strong>Đơn (P)</strong> để đặt điểm giao. Lộ trình xe chạy nối liền các điểm sẽ được tính toán tự động.
          </div>
        </section>

        {/* Khung bản đồ Canvas & Bảng so sánh */}
        <section style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* Màn hình hiển thị bản đồ */}
          <div className="glass-panel" style={{ padding: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2 style={{ fontSize: '1.1rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Grid size={18} style={{ color: 'var(--primary)' }} />
                Màn hình Mô phỏng Tuyến đường ({gridWidth}x{gridHeight})
              </h2>
              {mapLoading && <span style={{ fontSize: '0.85rem', color: 'var(--primary)' }}>Đang nạp dữ liệu bản đồ...</span>}
            </div>

            <div className="map-viewport">
              {/* Relative container đóng vai trò chứa Canvas và đặt ghim HTML Overlay siêu nét đè lên */}
              <div className="map-container-relative" style={{ width: canvasSize, height: canvasSize }}>
                <canvas 
                  ref={canvasRef} 
                  width={canvasSize} 
                  height={canvasSize}
                  onMouseDown={handleMouseDown}
                  onMouseMove={handleMouseMove}
                  onMouseUp={handleMouseUpOrLeave}
                  onMouseLeave={handleMouseUpOrLeave}
                />
                
                {/* Ghim Vị trí Kho Depot tuyệt đối (HTML Overlay) */}
                {depot && (
                  <div 
                    className="map-marker-absolute marker-bounce"
                    style={{
                      left: `${((depot.x + 0.5) / gridWidth) * 100}%`,
                      top: `${((depot.y + 0.5) / gridHeight) * 100}%`
                    }}
                  >
                    <div className="depot-marker-pin">
                      <Home size={15} />
                    </div>
                    <div className="marker-tooltip">Kho Depot trung tâm: ({depot.x}, {depot.y})</div>
                  </div>
                )}

                {/* Ghim các điểm cần giao hàng (HTML Overlay găm số) */}
                {deliveries.map((pt, idx) => (
                  <div 
                    className="map-marker-absolute marker-bounce"
                    key={idx}
                    style={{
                      left: `${((pt.x + 0.5) / gridWidth) * 100}%`,
                      top: `${((pt.y + 0.5) / gridHeight) * 100}%`
                    }}
                  >
                    <div className="delivery-marker-pin">
                      <span className="delivery-marker-text">{idx + 1}</span>
                    </div>
                    <div className="marker-tooltip">Địa chỉ giao hàng {idx + 1}: ({pt.x}, {pt.y})</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Kết quả thống kê lộ trình */}
          <div className="glass-panel">
            <h2 className="panel-title"><BarChart2 size={18} /> THỐNG KÊ KẾT QUẢ TỐI ƯU HÓA</h2>
            
            {tourIndices.length > 0 ? (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', color: 'hsl(188, 90%, 48%)' }}>
                  <CheckCircle size={18} />
                  <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>Đã tìm thấy lộ trình giao hàng tối ưu!</span>
                </div>
                
                <div style={{ background: 'hsl(223, 20%, 10%)', padding: '0.85rem 1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-light)', fontSize: '0.9rem', marginBottom: '1.5rem', lineHeight: '1.6' }}>
                  <strong>Hành trình chi tiết:</strong> Kho trung tâm Depot → {
                    tourIndices.slice(1, tourIndices.length - 1).map((idx, i) => (
                      <span key={i}>
                        <span style={{ color: 'var(--secondary)', fontWeight: 'bold' }}>Điểm {idx}</span> → 
                      </span>
                    ))
                  } Kho trung tâm Depot
                </div>

                <div className="metrics-grid">
                  <div className="metric-card">
                    <span className="metric-label">Tổng Chi Phí Hành Trình (Quãng đường + Tắc nghẽn)</span>
                    <span className="metric-value">{tourCost.toFixed(2)}<span className="metric-unit">cost</span></span>
                  </div>
                  <div className="metric-card">
                    <span className="metric-label">Tổng Số Điểm Giao Hàng</span>
                    <span className="metric-value" style={{ color: 'var(--secondary)' }}>{deliveries.length}<span className="metric-unit">địa chỉ</span></span>
                  </div>
                  <div className="metric-card">
                    <span className="metric-label">Heuristic tìm đường</span>
                    <span className="metric-value" style={{ color: 'var(--accent-gold)' }}>{selectedHeuristic}</span>
                  </div>
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', padding: '2rem', justifyContent: 'center' }}>
                <AlertTriangle size={20} />
                <span>Không tìm thấy đường đi. Đảm bảo các điểm dừng không nằm đè trên tường và có đường đi kết nối.</span>
              </div>
            )}

            {/* Bảng và Biểu đồ so sánh Heuristics */}
            {comparisonStats.length > 0 && (
              <div style={{ marginTop: '2rem', borderTop: '1px solid var(--border-light)', paddingTop: '1.5rem' }}>
                <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem', color: 'var(--text-primary)' }}>
                  Kết quả phân tích 3 Heuristics học thuật (Từ Depot → Điểm 1)
                </h3>
                
                {/* Bảng so sánh */}
                <div className="comparison-table-wrapper">
                  <table className="comparison-table">
                    <thead>
                      <tr>
                        <th>Hàm Heuristic</th>
                        <th>Độ dài / Chi phí đường đi</th>
                        <th>Số nút đã duyệt (Visited Nodes)</th>
                        <th>Thời gian chạy</th>
                      </tr>
                    </thead>
                    <tbody>
                      {comparisonStats.map(stat => {
                        const isBest = stat.expanded === Math.min(...comparisonStats.map(s => s.expanded));
                        return (
                          <tr key={stat.name} className={isBest ? "highlight" : ""}>
                            <td>
                              <strong>{stat.name} Distance</strong> {isBest && "🏆"}
                            </td>
                            <td>{stat.cost === Infinity ? "Không tìm thấy" : stat.cost.toFixed(2)}</td>
                            <td>{stat.expanded.toLocaleString()} ô</td>
                            <td>{stat.time.toFixed(2)} ms</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {/* Biểu đồ thanh trượt trực quan so sánh Số lượng Node đã duyệt */}
                <div className="chart-container">
                  <span className="chart-title">Biểu đồ so sánh số ô cần duyệt (Càng ít càng tối ưu):</span>
                  {comparisonStats.map(stat => {
                    const maxExpanded = Math.max(...comparisonStats.map(s => s.expanded)) || 1;
                    const percent = (stat.expanded / maxExpanded) * 100;
                    const isWinner = stat.expanded === Math.min(...comparisonStats.map(s => s.expanded));
                    return (
                      <div className="chart-row" key={stat.name}>
                        <span className="chart-label">{stat.name}</span>
                        <div className="chart-bar-bg">
                          <div 
                            className={`chart-bar-fill ${isWinner ? 'winner' : ''}`} 
                            style={{ width: `${percent}%` }}
                          >
                            <span className="chart-bar-value">{stat.expanded} ô</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
                
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '1rem', lineHeight: '1.4' }}>
                  * **Nhận xét học thuật**: Heuristic **Manhattan** phù hợp khi chỉ cho di chuyển 4 hướng (vuông góc). Đối với bản đồ cho phép di chuyển 8 hướng chéo, **Octile Distance** là heuristic tối ưu thực tế nhất vì phản ánh đúng chi phí đi chéo ($\sqrt{2}$). Nó giúp thu hẹp số lượng ô duyệt (vùng tìm kiếm vẽ màu xanh) và rút ngắn thời gian xử lý rõ rệt so với Dijkstra hay duyệt loang BFS thông thường.
                </p>
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
