import re

with open('baocao.txt', encoding='utf-8') as f:
    lines = f.readlines()

# Strip newlines for processing
lines = [l.rstrip('\r\n') for l in lines]

result = []
i = 0

def is_separator(s):
    """Dong phan cach chinh === hoac ---"""
    return re.match(r'^[=\-]{10,}$', s.strip()) is not None

def is_section_heading(s):
    """Heading cap 1, 2 hoac CHUONG, PHAN MO DAU, KET LUAN, TAI LIEU"""
    t = s.strip()
    return (re.match(r'^(CHƯƠNG|PHẦN MỞ|KẾT LUẬN|TÀI LIỆU)', t) is not None or
            re.match(r'^[1-9]\.\s+\S', t) is not None)

def is_heading3(s):
    """Heading cap 3: 1.1.1., 2.2.3., ..."""
    t = s.strip()
    return re.match(r'^\d+\.\d+\.\d+\.?\s+\S', t) is not None

def is_heading2(s):
    """Heading cap 2: 1.1., 2.2., ..."""
    t = s.strip()
    return re.match(r'^\d+\.\d+\.?\s+\S', t) is not None and not is_heading3(s)

def is_any_heading(s):
    return is_separator(s) or is_section_heading(s) or is_heading2(s) or is_heading3(s)

def is_dots_line(s):
    """Dong chi co dau cham hoac cach"""
    return re.match(r'^[\.\s]+$', s.strip()) is not None and len(s.strip()) > 3

n = len(lines)
i = 0

while i < n:
    line = lines[i]
    stripped = line.strip()

    # 1. Bỏ hẳn dòng chấm chấm
    if is_dots_line(stripped):
        i += 1
        continue

    # 2. Nếu là dòng trắng, xem context
    if stripped == '':
        # Lấy dòng thực trước và sau (bỏ qua dòng trắng liên tiếp)
        prev_real = ''
        for k in range(i - 1, -1, -1):
            if lines[k].strip():
                prev_real = lines[k].strip()
                break

        next_real = ''
        for k in range(i + 1, n):
            if lines[k].strip():
                next_real = lines[k].strip()
                break

        prev_is_sep   = is_separator(prev_real)
        prev_is_head  = is_any_heading(prev_real) and not is_separator(prev_real)
        next_is_sep   = is_separator(next_real)
        next_is_head  = is_any_heading(next_real)

        # Giữ 1 dòng trắng trước === / --- (phân cách section lớn)
        # Giữ 1 dòng trắng SAU === (sau dòng === header)
        # Bỏ dòng trắng sau heading (2/3) và giữa các đoạn văn thường

        keep = False

        # Dòng trắng trước separator lớn ===
        if next_is_sep and is_separator(next_real) and next_real.startswith('='):
            keep = True
        # Dòng trắng sau separator lớn ===
        if prev_is_sep and prev_real.startswith('='):
            keep = True
        # Dòng trắng trước separator --- (heading 1/2)
        if next_is_sep and next_real.startswith('-'):
            keep = True
        # Dòng trắng trước CHUONG, section heading
        if next_is_head and is_section_heading(next_real):
            keep = True
        # Dòng trắng trước heading 2 (không có --- vì --- đã đi sau)
        if next_is_head and is_heading2(next_real):
            keep = True
        # Dòng trắng sau ---
        if prev_is_sep and prev_real.startswith('-'):
            keep = True
        # Dòng trắng trước heading 3 (để tách rõ)
        if next_is_head and is_heading3(next_real):
            keep = True

        if keep:
            # Chỉ thêm 1 dòng trắng dù có nhiều dòng trắng liên tiếp
            if result and result[-1] != '':
                result.append('')
        # else: bỏ dòng trắng
        i += 1
        continue

    result.append(line)
    i += 1

# Gom dong trong thua
output = '\n'.join(result)
output = re.sub(r'\n{3,}', '\n\n', output)

with open('baocao.txt', 'w', encoding='utf-8') as f:
    f.write(output)

lc = output.count('\n')
sk = len(output.encode('utf-8')) // 1024
print(f'Done. Lines: {lc}, Size: {sk} KB')
