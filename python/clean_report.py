import re

with open('baocao.txt', encoding='utf-8') as f:
    text = f.read()

# Split into lines
lines = text.split('\n')
cleaned_lines = []

# Regex patterns for headings
# Heading 2 or 3 with digits: e.g., "1.1.", "1.1.1.", "1. "
heading_digit_pat = re.compile(r'^(\d+(\.\d+)*\.?)\s+(.*)$')
# Chapter / Major section headings
major_heading_pat = re.compile(r'^(CHƯƠNG|PHẦN|KẾT LUẬN|TÀI LIỆU|TRƯỜNG ĐẠI HỌC|KHOA CÔNG NGHỆ|BÁO CÁO BÀI TẬP|MÔN:|ĐỀ TÀI:|TỐI ƯU HÓA|BẰNG THUẬT TOÁN|\(DELIVERY|Nhóm sinh viên|Giảng viên|Năm học|HẾT)')

def is_divider(line):
    # If the line consists only of =, -, or . (at least 3 characters)
    stripped = line.strip()
    if not stripped:
        return False
    return all(c in '=-._' for c in stripped) and len(stripped) >= 3

# Step 1: Remove all divider lines and strip leading/trailing spaces for plain lines (except indent)
processed_lines = []
for line in lines:
    if is_divider(line):
        continue
    # Keep the line but strip trailing spaces
    processed_lines.append(line.rstrip())

# Step 2: Remove all blank lines entirely to avoid "cách 1 dòng trống"
# We will rebuild the lines without any empty lines.
non_empty_lines = [l for l in processed_lines if l.strip() != '']

# Step 3: Ensure 11-space indentation only on the first paragraph after heading 2 and heading 3.
# Let's define what heading 2 and heading 3 are.
# Heading 2: digit format like X.Y. or X.
# Heading 3: digit format like X.Y.Z.
# Any other line is a paragraph or major heading.
final_lines = []
next_paragraph_needs_indent = False

for idx, line in enumerate(non_empty_lines):
    stripped = line.strip()
    
    # Check if this line itself is a heading
    is_h_digit = heading_digit_pat.match(stripped)
    is_major = major_heading_pat.match(stripped)
    
    if is_h_digit:
        # It's a heading like 1.1., 1.1.1. or 1.
        # We output it clean (no leading spaces)
        final_lines.append(stripped)
        next_paragraph_needs_indent = True
    elif is_major:
        # Major heading
        final_lines.append(stripped)
        next_paragraph_needs_indent = False
    else:
        # It's a regular paragraph line or a list item
        if next_paragraph_needs_indent:
            # First paragraph after heading 2/3 gets exactly 11 spaces indent
            # But only if it's not a list item starting with '-'
            if not stripped.startswith('-') and not stripped.startswith('['):
                final_lines.append('           ' + stripped)
            else:
                final_lines.append(line) # Keep as is
            next_paragraph_needs_indent = False
        else:
            # Sub-paragraphs should NOT have the 11 spaces indent
            if line.startswith('           ') and not stripped.startswith('-'):
                final_lines.append(stripped)
            else:
                final_lines.append(line)

# Let's write this to baocao.txt
with open('baocao.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(final_lines))

print(f"Total lines: {len(final_lines)}")
