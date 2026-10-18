import os
import io
import base64
import qrcode
from PIL import Image, ImageDraw, ImageFont
from django.conf import settings
from django.http import HttpResponse


def get_base_url(request=None):
    """Resolve full base URL using request or default domain."""
    if request is not None:
        try:
            return request.build_absolute_uri('/')[:-1]
        except Exception:
            pass
    return getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000').rstrip('/')


def _get_font(size=16, bold=False):
    """Safely obtain a Truetype font or default font."""
    font_names = ['arialbd.ttf' if bold else 'arial.ttf', 'segoeui.ttf', 'DejaVuSans.ttf']
    for fn in font_names:
        try:
            return ImageFont.truetype(fn, size)
        except Exception:
            continue
    return ImageFont.load_default()


def create_center_logo(logo_path=None, size=80, primary_color='#0b2b4a'):
    """
    Generate an embedded circular logo emblem.
    If logo_path is provided and exists, uses the custom logo with a circular mask & white border.
    Otherwise generates the official Qenagebeya Ethiopian brand emblem.
    """
    if logo_path and os.path.exists(logo_path):
        try:
            base_img = Image.open(logo_path).convert('RGBA')
            min_dim = min(base_img.size)
            left = (base_img.width - min_dim) // 2
            top = (base_img.height - min_dim) // 2
            base_img = base_img.crop((left, top, left + min_dim, top + min_dim))
            base_img = base_img.resize((size - 8, size - 8), Image.Resampling.LANCZOS)
            
            # Mask to circle
            mask = Image.new('L', (size - 8, size - 8), 0)
            draw_m = ImageDraw.Draw(mask)
            draw_m.ellipse([0, 0, size - 8, size - 8], fill=255)
            
            logo = Image.new('RGBA', (size, size), (255, 255, 255, 0))
            draw = ImageDraw.Draw(logo)
            # White background circle with border
            draw.ellipse([0, 0, size - 1, size - 1], fill='#ffffff', outline='#cbd5e1', width=2)
            logo.paste(base_img, (4, 4), mask)
            return logo
        except Exception:
            pass

    # Default Qenagebeya Brand Emblem with Ethiopian Flag Accent
    logo = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(logo)
    
    # Outer white protective ring
    draw.ellipse([0, 0, size - 1, size - 1], fill='#ffffff')
    
    # Inner primary circle
    pad = 3
    draw.ellipse([pad, pad, size - 1 - pad, size - 1 - pad], fill=primary_color)
    
    # Flag color accent dots (Green, Gold/Yellow, Red)
    dot_r = max(2, size // 22)
    cx, cy = size // 2, size // 2
    top_y = pad + dot_r + 2
    draw.ellipse([cx - dot_r*3, top_y, cx - dot_r, top_y + dot_r*2], fill='#078930')
    draw.ellipse([cx - dot_r, top_y, cx + dot_r, top_y + dot_r*2], fill='#f59e0b')
    draw.ellipse([cx + dot_r, top_y, cx + dot_r*3, top_y + dot_r*2], fill='#d42e2e')
    
    font = _get_font(int(size * 0.44), bold=True)
    draw.text((cx, cy + size // 18), 'Q', fill='#ffffff', font=font, anchor='mm')
    return logo


def generate_qr_image(
    data_str,
    box_size=10,
    border=2,
    fill_color='#0b2b4a',
    back_color='#ffffff',
    logo_path=None,
    embed_logo=True
):
    """
    Generate QR code image with high error correction and embedded center logo.
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # 30% recovery capability
        box_size=box_size,
        border=border
    )
    qr.add_data(data_str)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fill_color, back_color=back_color).convert('RGBA')

    if embed_logo:
        qr_w, qr_h = img.size
        logo_size = int(qr_w * 0.24)  # ~24% of QR size for optimal scanning & brand visibility
        logo = create_center_logo(logo_path=logo_path, size=logo_size, primary_color=fill_color)
        pos = ((qr_w - logo.size[0]) // 2, (qr_h - logo.size[1]) // 2)
        img.paste(logo, pos, logo)

    return img


def generate_qr_data_uri(
    data_str,
    box_size=8,
    border=2,
    fill_color='#0b2b4a',
    back_color='#ffffff',
    logo_path=None,
    embed_logo=True
):
    """Generate base64 data URI string with embedded center logo for HTML templates."""
    img = generate_qr_image(
        data_str,
        box_size=box_size,
        border=border,
        fill_color=fill_color,
        back_color=back_color,
        logo_path=logo_path,
        embed_logo=embed_logo
    )
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{encoded}"


def generate_branded_badge_image(
    title,
    subtitle="",
    badge_type="PRODUCT",
    qr_data_str="",
    logo_path=None,
    footer="Qenagebeya.com 🇪🇹 · Ethiopian Marketplace",
    primary_color='#0b2b4a',
    secondary_color='#d42e2e'
):
    """
    Generate a high-resolution, printable 540x740 marketing flyer badge
    with Ethiopian flag accents, embedded logo QR code, and typography.
    """
    width, height = 540, 740
    badge = Image.new('RGBA', (width, height), color='#ffffff')
    draw = ImageDraw.Draw(badge)

    # 1. Outer Border / Card Outline
    draw.rectangle([0, 0, width - 1, height - 1], outline='#e2e8f0', width=2)

    # 2. Header Banner
    header_height = 120
    draw.rectangle([0, 0, width, header_height], fill=primary_color)
    
    # Ethiopian Tri-color Accent Ribbon at Header Bottom
    flag_h = 6
    seg_w = width // 3
    draw.rectangle([0, header_height - flag_h, seg_w, header_height], fill='#078930')
    draw.rectangle([seg_w, header_height - flag_h, seg_w * 2, header_height], fill='#f59e0b')
    draw.rectangle([seg_w * 2, header_height - flag_h, width, header_height], fill='#d42e2e')

    font_brand = _get_font(24, bold=True)
    font_badge_type = _get_font(12, bold=True)
    
    draw.text((28, 28), "QENAGEBEYA 🇪🇹", fill='#ffffff', font=font_brand)
    draw.text((28, 68), f"OFFICIAL {badge_type.upper()} VERIFICATION", fill='#93c5fd', font=font_badge_type)

    # 3. Title & Subtitle
    font_title = _get_font(21, bold=True)
    font_sub = _get_font(17, bold=True)
    font_cta = _get_font(14, bold=False)
    font_footer = _get_font(12, bold=False)

    display_title = title if len(title) <= 38 else title[:35] + "..."
    draw.text((28, header_height + 26), display_title, fill='#0f172a', font=font_title)

    if subtitle:
        draw.text((28, header_height + 60), subtitle, fill=secondary_color, font=font_sub)

    # 4. QR Code Box (Center) with Embedded Center Logo
    qr_img = generate_qr_image(
        qr_data_str,
        box_size=8,
        border=2,
        fill_color=primary_color,
        logo_path=logo_path,
        embed_logo=True
    )
    qr_w, qr_h = qr_img.size

    box_padding = 16
    box_x1 = (width - qr_w) // 2 - box_padding
    box_y1 = header_height + 110
    box_x2 = box_x1 + qr_w + (box_padding * 2)
    box_y2 = box_y1 + qr_h + (box_padding * 2)

    # Container background with subtle shadow simulation
    draw.rounded_rectangle([box_x1 + 3, box_y1 + 3, box_x2 + 3, box_y2 + 3], radius=20, fill='#f1f5f9')
    draw.rounded_rectangle([box_x1, box_y1, box_x2, box_y2], radius=20, fill='#ffffff', outline='#cbd5e1', width=2)
    
    # Paste QR Code
    qr_paste_x = (width - qr_w) // 2
    qr_paste_y = box_y1 + box_padding
    badge.paste(qr_img, (qr_paste_x, qr_paste_y), qr_img)

    # 5. CTA Pill Badge below QR
    cta_y = box_y2 + 24
    cta_text = "📷 Scan with Phone Camera to View & Connect"
    pill_w = 340
    pill_h = 32
    pill_x1 = (width - pill_w) // 2
    pill_y1 = cta_y - 16
    draw.rounded_rectangle([pill_x1, pill_y1, pill_x1 + pill_w, pill_y1 + pill_h], radius=16, fill='#f8fafc', outline='#e2e8f0', width=1)
    draw.text((width // 2, cta_y), cta_text, fill='#334155', font=font_cta, anchor="mm")

    # 6. Footer
    draw.line([30, height - 50, width - 30, height - 50], fill='#e2e8f0', width=1)
    draw.text((width // 2, height - 26), footer, fill='#94a3b8', font=font_footer, anchor="mm")

    return badge


def serve_qr_response(image_obj, filename="qr-code.png", as_download=False):
    """Helper to convert PIL Image to Django HttpResponse."""
    buffer = io.BytesIO()
    image_obj.save(buffer, format='PNG')
    response = HttpResponse(buffer.getvalue(), content_type='image/png')
    disposition = 'attachment' if as_download else 'inline'
    response['Content-Disposition'] = f'{disposition}; filename="{filename}"'
    return response
