import matplotlib.pyplot as plt
import os

output_dir = r"d:\CNTT\TRITUENHANTAO\BTL\IMG"
os.makedirs(output_dir, exist_ok=True)

def render_performance_table():
    columns = ["Heuristic", "Độ dài đường đi\n(Path Cost)", "Số nút đã duyệt\n(Nodes Expanded)", "Thời gian tính toán\n(Time in ms)"]
    data = [
        ["Manhattan", "237.47", "9,002", "260.74 ms"],
        ["Euclidean", "237.47", "12,854", "280.07 ms"],
        ["Chebyshev", "237.47", "14,421", "381.33 ms"],
        ["Octile", "237.47", "11,298", "298.28 ms"],
        ["Dijkstra", "237.47", "32,188", "677.83 ms"]
    ]

    fig, ax = plt.subplots(figsize=(10, 3.5), dpi=300)
    ax.axis('off')

    tbl = ax.table(
        cellText=data,
        colLabels=columns,
        loc='center',
        cellLoc='center',
        colWidths=[0.22, 0.26, 0.26, 0.26]
    )

    tbl.auto_set_font_size(False)
    tbl.set_fontsize(11)

    for (row, col), cell in tbl.get_celld().items():
        cell.set_text_props(fontfamily='DejaVu Sans', va='center', ha='center')
        if row == 0:
            cell.set_text_props(weight='bold', color='white', fontsize=11)
            cell.set_facecolor('#1e293b')  # Dark slate header
            cell.set_edgecolor('#0f172a')
            cell.set_height(0.20)
        else:
            cell.set_edgecolor('#cbd5e1')
            cell.set_height(0.15)
            if row % 2 == 1:
                cell.set_facecolor('#f8fafc')
            else:
                cell.set_facecolor('#ffffff')
            
            # Make Octile stand out as optimal or Dijkstra stand out as slowest
            val = cell.get_text().get_text()
            if row == 4: # Octile (1-indexed row 4 is Octile)
                # Bold Octile row to highlight it
                cell.set_facecolor('#f0fdf4') # Soft green highlight for Octile
            if col == 0:
                cell.set_text_props(weight='bold')

    plt.tight_layout()
    output_path = os.path.join(output_dir, "table_performance.png")
    plt.savefig(output_path, bbox_inches='tight', transparent=True)
    plt.close()
    print(f"Performance table saved to: {output_path}")

def render_traffic_table():
    columns = ["Khung giờ", "Mức độ ùn tắc", "Chi phí lộ trình\n(Tránh kẹt xe)", "Chi phí lộ trình\n(Đi thẳng qua vùng kẹt)", "Hiệu quả cải thiện"]
    data = [
        ["00:00 - Đêm", "Thông thoáng (x1.0)", "237.47", "237.47", "0.0% (Không kẹt)"],
        ["08:00 - Sáng", "Cao điểm (x4.0)", "345.82", "582.14", "40.6% (Né kẹt xe)"],
        ["12:00 - Trưa", "Cao điểm (x5.0)", "312.15", "495.60", "37.0% (Né kẹt xe)"],
        ["18:00 - Chiều", "Cao điểm (x4.0)", "354.20", "598.30", "40.8% (Né kẹt xe)"]
    ]

    fig, ax = plt.subplots(figsize=(10, 3.5), dpi=300)
    ax.axis('off')

    tbl = ax.table(
        cellText=data,
        colLabels=columns,
        loc='center',
        cellLoc='center',
        colWidths=[0.20, 0.20, 0.20, 0.20, 0.20]
    )

    tbl.auto_set_font_size(False)
    tbl.set_fontsize(11)

    for (row, col), cell in tbl.get_celld().items():
        cell.set_text_props(fontfamily='DejaVu Sans', va='center', ha='center')
        if row == 0:
            cell.set_text_props(weight='bold', color='white', fontsize=11)
            cell.set_facecolor('#1e293b')
            cell.set_edgecolor('#0f172a')
            cell.set_height(0.20)
        else:
            cell.set_edgecolor('#cbd5e1')
            cell.set_height(0.15)
            if row % 2 == 1:
                cell.set_facecolor('#f8fafc')
            else:
                cell.set_facecolor('#ffffff')
            
            if col == 4 and row > 1:
                cell.get_text().set_color('#16a34a')
                cell.get_text().set_weight('bold')

    plt.tight_layout()
    output_path = os.path.join(output_dir, "table_traffic.png")
    plt.savefig(output_path, bbox_inches='tight', transparent=True)
    plt.close()
    print(f"Traffic table saved to: {output_path}")

if __name__ == "__main__":
    render_performance_table()
    render_traffic_table()
