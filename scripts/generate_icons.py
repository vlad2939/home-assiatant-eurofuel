import os
from PIL import Image

def make_background_transparent(src_path, dest_dir):
    print(f"Loading generated image from: {src_path}")
    img = Image.open(src_path).convert("RGBA")
    
    # Soft keying to remove black background smoothly
    datas = img.getdata()
    newData = []
    for item in datas:
        r, g, b, a = item
        # Calculate brightness/distance from black
        brightness = max(r, g, b)
        if brightness < 20:
            newData.append((0, 0, 0, 0))
        elif brightness < 50:
            # Linear alpha fade for smooth edges
            alpha = int((brightness - 20) / (50 - 20) * 255)
            # Retain color but scale alpha
            newData.append((r, g, b, alpha))
        else:
            newData.append((r, g, b, 255))
            
    img.putdata(newData)
    
    # Create img directory if it doesn't exist
    img_dir = os.path.join(dest_dir, "img")
    if not os.path.exists(img_dir):
        os.makedirs(img_dir)
        
    # 1. Save transparent PNG Logo
    logo_path = os.path.join(img_dir, "logo.png")
    img.save(logo_path, "PNG")
    print(f"Saved logo: {logo_path}")
    
    # 2. Save desktop shortcut Windows ICO (256x256, 48x48, 32x32, 16x16)
    ico_path = os.path.join(dest_dir, "icon.ico")
    sizes = [(256, 256), (48, 48), (32, 32), (16, 16)]
    img.save(ico_path, format="ICO", sizes=sizes)
    print(f"Saved Windows Shortcut ICO: {ico_path}")
    
    # 3. Save Web Favicon ICO (32x32)
    favicon_path = os.path.join(dest_dir, "favicon.ico")
    img.save(favicon_path, format="ICO", sizes=[(32, 32)])
    print(f"Saved favicon.ico: {favicon_path}")
    
    # 4. Save PNG Favicon (32x32)
    fav_png_path = os.path.join(img_dir, "favicon-32x32.png")
    favicon_img = img.resize((32, 32), Image.Resampling.LANCZOS)
    favicon_img.save(fav_png_path, "PNG")
    print(f"Saved PNG Favicon: {fav_png_path}")

if __name__ == "__main__":
    src_img = r"C:\Users\Vlad\.gemini\antigravity\brain\508e458c-da2b-43a3-8226-1f28699efed6\gas_pump_3d_icon_1781570097316.png"
    project_dir = r"c:\Users\Vlad\Documents\Antigravity\euro_fuel"
    make_background_transparent(src_img, project_dir)
