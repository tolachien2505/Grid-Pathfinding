import matplotlib.pyplot as plt
import os

output_dir = r"d:\CNTT\TRITUENHANTAO\BTL\IMG"
os.makedirs(output_dir, exist_ok=True)

def render_heuristics_table():
    # Data definition
    columns = ["Heuristic", "Admissible", "Consistent", "Độ chính xác ước lượng\n(Lưới 8 hướng)"]
    data = [
        ["Manhattan", "Có", "Có", "Thấp (underest.)"],
        ["Euclidean", "Có", "Có", "Trung bình"],
        ["Chebyshev", "Không", "Không", "Cao (có thể overest)"],
        ["Octile", "Có", "Có", "Cao nhất (tối ưu)"],
        ["Dijkstra", "Có (h=0)", "Có", "Thấp nhất (0)"]
    ]

    # Create figure and axis
    fig, ax = plt.subplots(figsize=(10, 3.5), dpi=300)
    ax.axis('off')

    # Draw table
    tbl = ax.table(
        cellText=data,
        colLabels=columns,
        loc='center',
        cellLoc='center',
        colWidths=[0.20, 0.18, 0.18, 0.44]
    )

    # Style table cells
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(11)

    # Apply premium colors & styling
    for (row, col), cell in tbl.get_celld().items():
        cell.set_text_props(fontfamily='DejaVu Sans', va='center', ha='center')
        if row == 0:
            # Header styling
            cell.set_text_props(weight='bold', color='white', fontsize=11)
            cell.set_facecolor('#1e293b')  # Dark slate
            cell.set_edgecolor('#0f172a')
            cell.set_height(0.20)
        else:
            # Body rows styling
            cell.set_edgecolor('#cbd5e1')
            cell.set_height(0.15)
            # Alternating row colors
            if row % 2 == 1:
                cell.set_facecolor('#f8fafc')  # Very light slate/gray
            else:
                cell.set_facecolor('#ffffff')
            
            # Color specific values for contrast
            val = cell.get_text().get_text()
            if val == "Có" or val == "Có (h=0)":
                cell.get_text().set_color('#16a34a') # Green
                cell.get_text().set_weight('bold')
            elif val == "Không":
                cell.get_text().set_color('#dc2626') # Red
                cell.get_text().set_weight('bold')

    plt.tight_layout()
    output_path = os.path.join(output_dir, "table_heuristics.png")
    plt.savefig(output_path, bbox_inches='tight', transparent=True)
    plt.close()
    print(f"Table image rendered successfully and saved to: {output_path}")

if __name__ == "__main__":
    render_heuristics_table()
