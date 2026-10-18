"""
File analysis utilities for Makerspace.

Supported:
  .stl  — 3D mesh → volume (cm³) → grams at given infill %
  .obj  — 3D mesh → same as STL
  .dxf  — 2D drawing → bounding-box area estimate (cm²)
  .svg  — 2D vector → bounding-box area estimate (cm²)
  .pdf  — 2D document → A4 area default
  .dwg / .step / .iges — header inspection only (return defaults)

Material densities (g/cm³):
  PLA   = 1.24
  PETG  = 1.27
  ABS   = 1.05
  Resin = 1.10
  Wood  = 0.60
  Acrylic = 1.18
  Aluminum = 2.70
"""

import os
import struct
import logging

log = logging.getLogger(__name__)

DENSITIES = {
    '3d_pla':    1.24,
    '3d_petg':   1.27,
    '3d_abs':    1.05,
    '3d_resin':  1.10,
    'laser_wood':    0.60,
    'laser_acrylic': 1.18,
    'laser_metal':   7.80,
    'cnc_wood':      0.60,
    'cnc_aluminum':  2.70,
    'none':          1.00,
}


# ── STL Parser (pure Python, no trimesh required) ────────────────────────────

def _stl_volume_cm3(filepath: str) -> float:
    """
    Read an STL file (binary or ASCII) and compute signed volume in cm³.
    Uses the divergence theorem on each triangle.
    """
    try:
        with open(filepath, 'rb') as f:
            header = f.read(80)
            # Try binary STL
            try:
                num_triangles = struct.unpack('<I', f.read(4))[0]
                if num_triangles < 1 or num_triangles > 5_000_000:
                    raise ValueError('unlikely triangle count')
                volume_mm3 = 0.0
                for _ in range(num_triangles):
                    data = f.read(50)
                    if len(data) < 50:
                        break
                    # skip normal (12 bytes), read 3 vertices (36 bytes), skip attr (2 bytes)
                    v1 = struct.unpack('<3f', data[12:24])
                    v2 = struct.unpack('<3f', data[24:36])
                    v3 = struct.unpack('<3f', data[36:48])
                    # Signed volume contribution of this triangle
                    volume_mm3 += _signed_volume_triangle(v1, v2, v3)
                volume_cm3 = abs(volume_mm3) / 1000.0   # mm³ → cm³
                return max(volume_cm3, 0.01)
            except Exception:
                pass

        # Try ASCII STL
        with open(filepath, 'r', errors='ignore') as f:
            text = f.read()
        if 'facet normal' in text.lower():
            return _stl_ascii_volume(text)

    except Exception as e:
        log.warning(f'STL parse failed: {e}')

    return 0.0


def _signed_volume_triangle(v1, v2, v3) -> float:
    """Signed volume of tetrahedron formed by triangle and origin."""
    x1, y1, z1 = v1
    x2, y2, z2 = v2
    x3, y3, z3 = v3
    return (x1 * (y2 * z3 - y3 * z2)
          + x2 * (y3 * z1 - y1 * z3)
          + x3 * (y1 * z2 - y2 * z1)) / 6.0


def _stl_ascii_volume(text: str) -> float:
    """Parse ASCII STL and compute volume."""
    import re
    vertices = re.findall(r'vertex\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)', text)
    volume_mm3 = 0.0
    for i in range(0, len(vertices) - 2, 3):
        v1 = tuple(float(x) for x in vertices[i])
        v2 = tuple(float(x) for x in vertices[i + 1])
        v3 = tuple(float(x) for x in vertices[i + 2])
        volume_mm3 += _signed_volume_triangle(v1, v2, v3)
    return abs(volume_mm3) / 1000.0


def _try_trimesh_volume(filepath: str) -> float:
    """Use trimesh as a fallback for OBJ/STEP etc."""
    try:
        import trimesh
        mesh = trimesh.load(filepath, force='mesh')
        if hasattr(mesh, 'volume') and mesh.volume > 0:
            # trimesh uses mm³ if the file is in mm, otherwise assume m³
            vol = mesh.volume
            # Heuristic: if > 1e6, probably mm³
            if vol > 1e6:
                vol /= 1000.0   # mm³ → cm³
            elif vol < 0.001:
                vol *= 1e6      # m³ → cm³
            return max(float(vol), 0.01)
    except Exception as e:
        log.warning(f'trimesh failed: {e}')
    return 0.0


# ── SVG area estimator ────────────────────────────────────────────────────────

def _svg_area_cm2(filepath: str) -> float:
    """Extract viewBox / width+height from SVG, return area in cm²."""
    try:
        import re
        with open(filepath, 'r', errors='ignore') as f:
            content = f.read(4096)

        def parse_mm(val_str):
            val_str = val_str.strip()
            if val_str.endswith('mm'):
                return float(val_str[:-2])
            elif val_str.endswith('cm'):
                return float(val_str[:-2]) * 10
            elif val_str.endswith('in'):
                return float(val_str[:-2]) * 25.4
            elif val_str.endswith('px'):
                return float(val_str[:-2]) * 0.264583
            else:
                try:
                    return float(val_str) * 0.264583   # assume px
                except ValueError:
                    return 0.0

        # Try viewBox
        vb = re.search(r'viewBox=["\']([^"\']+)["\']', content)
        if vb:
            parts = vb.group(1).split()
            if len(parts) == 4:
                w_mm = float(parts[2])
                h_mm = float(parts[3])
                return (w_mm / 10) * (h_mm / 10)

        # Try width + height attributes
        w_m = re.search(r'<svg[^>]+width=["\']([^"\']+)["\']', content)
        h_m = re.search(r'<svg[^>]+height=["\']([^"\']+)["\']', content)
        if w_m and h_m:
            w_mm = parse_mm(w_m.group(1))
            h_mm = parse_mm(h_m.group(1))
            if w_mm > 0 and h_mm > 0:
                return (w_mm / 10) * (h_mm / 10)
    except Exception as e:
        log.warning(f'SVG parse failed: {e}')
    return 100.0   # default 10cm × 10cm


# ── DXF area estimator ────────────────────────────────────────────────────────

def _dxf_area_cm2(filepath: str) -> float:
    """
    Rough DXF bounding box from EXTMIN/EXTMAX.
    Returns area in cm².
    """
    try:
        with open(filepath, 'r', errors='ignore') as f:
            content = f.read()

        import re
        # Look for $EXTMIN and $EXTMAX in the header
        def get_group(section, group_code):
            pattern = rf'{re.escape(section)}.*?{group_code}\s*\n\s*([-\d.eE+]+)'
            m = re.search(pattern, content, re.DOTALL)
            return float(m.group(1)) if m else None

        x1 = get_group('$EXTMIN', ' 10')
        y1 = get_group('$EXTMIN', ' 20')
        x2 = get_group('$EXTMAX', ' 10')
        y2 = get_group('$EXTMAX', ' 20')

        if x1 is not None and y1 is not None and x2 is not None and y2 is not None:
            w_mm = abs(x2 - x1)
            h_mm = abs(y2 - y1)
            # If values look like they're in mm (>1), convert to cm
            if w_mm > 0.1 and h_mm > 0.1:
                return (w_mm / 10.0) * (h_mm / 10.0)
    except Exception as e:
        log.warning(f'DXF parse failed: {e}')
    return 100.0  # default 10cm × 10cm


# ── Main entry point ──────────────────────────────────────────────────────────

def analyse_file(filepath: str, service_type: str, material: str, infill: int = 30):
    """
    Analyse an uploaded design file and return a dict:
      {
        'volume_cm3':  float,
        'area_cm2':    float,
        'grams':       float,
        'file_type':   str,
        'error':       str or None,
      }
    """
    result = {
        'volume_cm3': 0.0,
        'area_cm2':   0.0,
        'grams':      0.0,
        'file_type':  '',
        'error':      None,
    }

    if not filepath or not os.path.exists(filepath):
        result['error'] = 'File not found'
        return result

    ext = os.path.splitext(filepath)[1].lower().lstrip('.')
    result['file_type'] = ext

    density = DENSITIES.get(material, 1.24)
    infill_factor = infill / 100.0

    if ext == 'stl':
        vol = _stl_volume_cm3(filepath)
        result['volume_cm3'] = vol
        result['grams'] = vol * density * infill_factor

    elif ext == 'obj':
        vol = _try_trimesh_volume(filepath)
        result['volume_cm3'] = vol
        result['grams'] = vol * density * infill_factor

    elif ext in ('step', 'stp', 'iges', 'igs'):
        vol = _try_trimesh_volume(filepath)
        result['volume_cm3'] = vol
        result['grams'] = vol * density * infill_factor
        if vol == 0:
            result['error'] = 'Could not auto-calculate from this file type. Vendor will quote manually.'

    elif ext == 'dxf':
        area = _dxf_area_cm2(filepath)
        result['area_cm2'] = area

    elif ext == 'svg':
        area = _svg_area_cm2(filepath)
        result['area_cm2'] = area

    elif ext == 'dwg':
        result['area_cm2'] = 100.0
        result['error'] = 'DWG binary format — area estimated at 100 cm². Vendor will confirm.'

    elif ext == 'pdf':
        result['area_cm2'] = 623.7   # A4 = 21cm × 29.7cm
        result['error'] = 'PDF: assuming A4 size. Vendor will confirm dimensions.'

    else:
        result['error'] = f'Unknown file type .{ext}. Vendor will quote manually.'

    return result


# ── Price calculator ──────────────────────────────────────────────────────────

def calculate_price(analysis: dict, service_type: str, material: str,
                    infill: int, quantity: int, profile) -> float:
    """
    Calculate estimated price in ETB based on analysis result and vendor profile.
    Returns float.
    """
    from decimal import Decimal

    q = max(1, quantity)

    if service_type == '3d_print':
        grams = float(analysis.get('grams', 0)) or 1.0
        price_per_g = float(profile.price_per_gram(material))
        # Infill adjustment (more infill = more material)
        base = grams * price_per_g * q
        # Minimum price ETB 80
        return max(base, 80.0)

    elif service_type == 'laser':
        area = float(analysis.get('area_cm2', 100)) or 100.0
        price_per_cm2 = float(profile.price_laser_per_cm2)
        return max(area * price_per_cm2 * q, 80.0)

    elif service_type == 'cnc':
        area = float(analysis.get('area_cm2', 100)) or 100.0
        price_per_cm2 = float(profile.price_cnc_per_cm2)
        return max(area * price_per_cm2 * q, 150.0)

    elif service_type == 'design':
        return float(profile.price_design_service) * q

    else:
        return 200.0   # custom / other: flat minimum
