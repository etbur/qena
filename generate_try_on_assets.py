import os
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

os.makedirs('media/try_on', exist_ok=True)

def create_female_model():
    # 600x900 female model portrait in neutral studio lighting
    im = Image.new('RGBA', (600, 900), (245, 247, 250, 255))
    draw = ImageDraw.Draw(im)
    
    # Soft background gradient
    for y in range(900):
        alpha = int(245 - (y / 900) * 15)
        draw.line([(0, y), (600, y)], fill=(alpha, alpha + 2, alpha + 5, 255))
    
    # Studio lighting circle backdrop
    draw.ellipse([80, 100, 520, 580], fill=(235, 240, 248, 255))
    
    skin_tone = (210, 160, 130, 255)
    skin_shadow = (185, 135, 105, 255)
    hair_color = (30, 20, 15, 255)
    
    # Hair back
    draw.ellipse([220, 80, 380, 300], fill=hair_color)
    
    # Head & Face
    draw.ellipse([240, 110, 360, 245], fill=skin_tone)
    # Neck
    draw.polygon([(270, 225), (330, 225), (340, 295), (260, 295)], fill=skin_tone)
    draw.polygon([(270, 225), (330, 225), (315, 255), (285, 255)], fill=skin_shadow)
    
    # Shoulders & Torso
    draw.polygon([(170, 305), (430, 305), (405, 480), (370, 680), (230, 680), (195, 480)], fill=(225, 228, 235, 255))
    
    # Arms
    draw.polygon([(170, 305), (195, 315), (155, 580), (130, 560)], fill=skin_tone)
    draw.polygon([(430, 305), (405, 315), (445, 580), (470, 560)], fill=skin_tone)
    
    # Legs
    draw.polygon([(230, 680), (295, 680), (285, 890), (235, 890)], fill=(60, 70, 85, 255))
    draw.polygon([(305, 680), (370, 680), (365, 890), (315, 890)], fill=(60, 70, 85, 255))
    
    # Hair styling & Face details
    draw.ellipse([235, 95, 365, 175], fill=hair_color)
    draw.arc([265, 170, 290, 180], start=0, end=180, fill=(60, 40, 30, 255), width=2)
    draw.arc([310, 170, 335, 180], start=0, end=180, fill=(60, 40, 30, 255), width=2)
    draw.arc([282, 205, 318, 218], start=10, end=170, fill=(180, 90, 80, 255), width=3)
    
    # Badge
    draw.rectangle([20, 20, 180, 50], fill=(11, 43, 74, 220))
    draw.text((32, 28), "SAMPLE MODEL (F)", fill=(255, 255, 255, 255))
    
    im.save('media/try_on/model_female.png', 'PNG')
    print("Created model_female.png")

def create_male_model():
    im = Image.new('RGBA', (600, 900), (245, 247, 250, 255))
    draw = ImageDraw.Draw(im)
    
    for y in range(900):
        alpha = int(245 - (y / 900) * 15)
        draw.line([(0, y), (600, y)], fill=(alpha, alpha + 2, alpha + 5, 255))
        
    draw.ellipse([70, 90, 530, 590], fill=(235, 240, 248, 255))
    
    skin_tone = (195, 145, 115, 255)
    skin_shadow = (170, 120, 90, 255)
    hair_color = (25, 20, 20, 255)
    
    draw.ellipse([235, 105, 365, 235], fill=skin_tone)
    draw.ellipse([230, 90, 370, 155], fill=hair_color)
    draw.polygon([(260, 215), (340, 215), (350, 285), (250, 285)], fill=skin_tone)
    
    draw.polygon([(135, 290), (465, 290), (425, 510), (390, 690), (210, 690), (175, 510)], fill=(230, 235, 242, 255))
    draw.polygon([(135, 290), (170, 305), (130, 590), (100, 570)], fill=skin_tone)
    draw.polygon([(465, 290), (430, 305), (470, 590), (500, 570)], fill=skin_tone)
    
    draw.polygon([(210, 690), (290, 690), (280, 890), (220, 890)], fill=(40, 55, 80, 255))
    draw.polygon([(310, 690), (390, 690), (380, 890), (320, 890)], fill=(40, 55, 80, 255))
    
    draw.arc([260, 160, 285, 170], start=0, end=180, fill=(50, 35, 30, 255), width=2)
    draw.arc([315, 160, 340, 170], start=0, end=180, fill=(50, 35, 30, 255), width=2)
    draw.arc([278, 200, 322, 210], start=10, end=170, fill=(160, 80, 70, 255), width=3)
    
    draw.rectangle([20, 20, 180, 50], fill=(11, 43, 74, 220))
    draw.text((32, 28), "SAMPLE MODEL (M)", fill=(255, 255, 255, 255))
    
    im.save('media/try_on/model_male.png', 'PNG')
    print("Created model_male.png")

def create_habesha_kemis_overlay():
    # 500x700 transparent cutout of Habesha Kemis
    im = Image.new('RGBA', (500, 700), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    
    # Main White Sheer Fabric Dress with Gold/Red Tibeb Embroidery
    dress_points = [
        (160, 45), (210, 75), (290, 75), (340, 45),
        (405, 135), (365, 225), (330, 215),
        (340, 335),
        (440, 665), (60, 665),
        (160, 335), (170, 215), (95, 225), (135, 135)
    ]
    draw.polygon(dress_points, fill=(253, 253, 255, 250), outline=(220, 220, 230, 255))
    
    # Gold & Ethiopian Tibeb Borders
    draw.line([(200, 78), (250, 145), (300, 78)], fill=(218, 165, 32, 255), width=10)
    draw.line([(205, 83), (250, 140), (295, 83)], fill=(212, 46, 46, 255), width=4)
    draw.line([(210, 88), (250, 135), (290, 88)], fill=(7, 137, 48, 255), width=3)
    
    # Medallion
    draw.ellipse([235, 165, 265, 195], fill=(218, 165, 32, 255))
    draw.rectangle([247, 155, 253, 205], fill=(212, 46, 46, 255))
    draw.rectangle([232, 177, 268, 183], fill=(7, 137, 48, 255))
    
    # Mekenet Sash
    draw.polygon([(158, 330), (342, 330), (338, 355), (162, 355)], fill=(218, 165, 32, 255))
    draw.line([(158, 342), (342, 342)], fill=(212, 46, 46, 255), width=4)
    
    # Grand Skirt Tibeb
    draw.polygon([(60, 615), (440, 615), (440, 665), (60, 665)], fill=(218, 165, 32, 255))
    draw.line([(60, 627), (440, 627)], fill=(7, 137, 48, 255), width=6)
    draw.line([(60, 640), (440, 640)], fill=(245, 158, 11, 255), width=6)
    draw.line([(60, 653), (440, 653)], fill=(212, 46, 46, 255), width=6)
    
    # Cuffs
    draw.polygon([(95, 210), (140, 185), (150, 205), (105, 230)], fill=(218, 165, 32, 255))
    draw.polygon([(405, 210), (360, 185), (350, 205), (395, 230)], fill=(218, 165, 32, 255))
    
    im.save('media/try_on/overlay_kemis.png', 'PNG')
    print("Created overlay_kemis.png")

def create_gabi_overlay():
    # 520x600 transparent cutout of Ethiopian Traditional Gabi / Netela Shawl Blanket
    # Draped elegantly around shoulders and chest
    im = Image.new('RGBA', (520, 600), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    
    # Soft warm textured white woven cotton blanket draped across torso
    gabi_points = [
        (130, 40), (260, 25), (390, 40),      # Back collar
        (470, 120), (450, 280), (390, 480),   # Right drape cascade
        (330, 540), (260, 520), (190, 540),   # Bottom V-shaped fold
        (130, 480), (70, 280), (50, 120)      # Left drape cascade
    ]
    draw.polygon(gabi_points, fill=(250, 248, 242, 245), outline=(220, 215, 200, 255))
    
    # Diagonal wrap cross fold (left shoulder over chest)
    wrap_fold = [
        (130, 40), (360, 360), (300, 420), (70, 200)
    ]
    draw.polygon(wrap_fold, fill=(244, 240, 232, 250))
    
    # Ethiopian Flag Colored Tibeb Woven Edges (Green, Yellow, Red) along the hem and collar
    # Right border
    draw.line([(470, 120), (450, 280), (390, 480), (330, 540)], fill=(7, 137, 48, 255), width=5)
    draw.line([(464, 120), (444, 280), (384, 480), (324, 540)], fill=(245, 158, 11, 255), width=5)
    draw.line([(458, 120), (438, 280), (378, 480), (318, 540)], fill=(212, 46, 46, 255), width=5)
    
    # Left border
    draw.line([(50, 120), (70, 280), (130, 480), (190, 540)], fill=(7, 137, 48, 255), width=5)
    draw.line([(56, 120), (76, 280), (136, 480), (196, 540)], fill=(245, 158, 11, 255), width=5)
    draw.line([(62, 120), (82, 280), (142, 480), (202, 540)], fill=(212, 46, 46, 255), width=5)
    
    # Fringes at bottom hem
    for x in range(180, 340, 6):
        draw.line([(x, 520), (x + 2, 560)], fill=(210, 200, 185, 255), width=2)
        
    im.save('media/try_on/overlay_gabi.png', 'PNG')
    print("Created overlay_gabi.png")

def create_kandura_overlay():
    im = Image.new('RGBA', (500, 700), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    
    kandura_points = [
        (180, 40), (225, 60), (275, 60), (320, 40),
        (420, 110), (370, 220), (340, 200),
        (335, 360),
        (370, 680), (130, 680),
        (165, 360), (160, 200), (130, 220), (80, 110)
    ]
    draw.polygon(kandura_points, fill=(255, 255, 255, 250), outline=(215, 220, 228, 255))
    
    draw.rectangle([230, 58, 270, 72], fill=(245, 245, 250, 255), outline=(200, 205, 215, 255))
    draw.line([(250, 72), (250, 190)], fill=(225, 230, 240, 255), width=3)
    draw.line([(250, 75), (265, 140)], fill=(200, 205, 215, 255), width=3)
    draw.ellipse([260, 135, 270, 150], fill=(200, 205, 215, 255))
    
    draw.rectangle([290, 115, 330, 150], outline=(220, 225, 235, 255), width=2)
    
    im.save('media/try_on/overlay_kandura.png', 'PNG')
    print("Created overlay_kandura.png")

def create_sheila_scarf_overlay():
    im = Image.new('RGBA', (500, 500), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    
    points = [
        (120, 80), (250, 50), (380, 80),
        (430, 220), (390, 420), (340, 450), (310, 300),
        (250, 280), (190, 300), (160, 450), (110, 420), (70, 220)
    ]
    draw.polygon(points, fill=(248, 242, 235, 240), outline=(210, 195, 180, 255))
    
    for y in [120, 180, 240, 320, 400]:
        draw.arc([130, y-30, 190, y+30], 0, 360, fill=(218, 165, 32, 200), width=3)
        draw.arc([310, y-30, 370, y+30], 0, 360, fill=(218, 165, 32, 200), width=3)
        
    for x in range(110, 160, 6):
        draw.line([(x, 430), (x, 460)], fill=(200, 180, 150, 255), width=2)
    for x in range(340, 390, 6):
        draw.line([(x, 430), (x, 460)], fill=(200, 180, 150, 255), width=2)
        
    im.save('media/try_on/overlay_sheila.png', 'PNG')
    im.save('media/try_on/overlay_scarf.png', 'PNG')
    print("Created overlay_sheila.png and overlay_scarf.png")

def create_mesob_overlay():
    # 400x480 transparent cutout of Traditional Mesob basket craft
    im = Image.new('RGBA', (400, 480), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    
    # Conical Lid
    lid_points = [(200, 30), (320, 210), (80, 210)]
    draw.polygon(lid_points, fill=(230, 180, 110, 255), outline=(180, 130, 70, 255))
    
    # Lid Handle
    draw.ellipse([185, 15, 215, 45], fill=(160, 50, 50, 255))
    
    # Geometric Diamond Patterns on Lid (Red, Blue, Green, Yellow)
    draw.polygon([(200, 70), (240, 140), (200, 180), (160, 140)], fill=(200, 40, 40, 255))
    draw.polygon([(200, 90), (225, 140), (200, 165), (175, 140)], fill=(240, 200, 40, 255))
    draw.polygon([(200, 110), (210, 140), (200, 150), (190, 140)], fill=(30, 140, 60, 255))
    
    # Cylindrical Base Basket
    base_points = [(90, 210), (310, 210), (290, 420), (110, 420)]
    draw.polygon(base_points, fill=(225, 175, 105, 255), outline=(180, 130, 70, 255))
    
    # Base Bands & diamonds
    draw.rectangle([95, 270, 305, 300], fill=(180, 40, 40, 255))
    draw.rectangle([100, 340, 300, 370], fill=(30, 130, 60, 255))
    
    im.save('media/try_on/overlay_mesob.png', 'PNG')
    print("Created overlay_mesob.png")

create_female_model()
create_male_model()
create_habesha_kemis_overlay()
create_gabi_overlay()
create_kandura_overlay()
create_sheila_scarf_overlay()
create_mesob_overlay()
print("All transparent cutout overlays generated successfully!")
