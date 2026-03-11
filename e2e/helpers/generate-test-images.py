"""Generate realistic test images for E2E screenshot showcase."""

import struct
import zlib
import os
import math
import random

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "test-images")


def make_png(width, height, pixels_rgb):
    """Create a PNG file from raw RGB pixel data."""
    def make_chunk(chunk_type, data):
        chunk = chunk_type + data
        crc = struct.pack('>I', zlib.crc32(chunk) & 0xFFFFFFFF)
        return struct.pack('>I', len(data)) + chunk + crc

    header = b'\x89PNG\r\n\x1a\n'
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr = make_chunk(b'IHDR', ihdr_data)

    raw_data = b''
    for y in range(height):
        raw_data += b'\x00'  # filter byte
        for x in range(width):
            idx = (y * width + x) * 3
            raw_data += bytes(pixels_rgb[idx:idx+3])

    compressed = zlib.compress(raw_data)
    idat = make_chunk(b'IDAT', compressed)
    iend = make_chunk(b'IEND', b'')

    return header + ihdr + idat + iend


def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def gradient_image(width, height, colors):
    """Create a gradient image with multiple color stops."""
    pixels = bytearray(width * height * 3)
    n = len(colors)
    for y in range(height):
        for x in range(width):
            t = x / max(width - 1, 1)
            seg = t * (n - 1)
            i = min(int(seg), n - 2)
            local_t = seg - i
            r, g, b = lerp_color(colors[i], colors[i+1], local_t)

            # Add slight vertical variation
            vy = y / max(height - 1, 1)
            r = max(0, min(255, r - int(40 * vy)))
            g = max(0, min(255, g - int(20 * vy)))
            b = max(0, min(255, b + int(30 * vy)))

            idx = (y * width + x) * 3
            pixels[idx] = r
            pixels[idx+1] = g
            pixels[idx+2] = b
    return make_png(width, height, pixels)


def landscape_image(width, height):
    """Create a mountain landscape scene."""
    pixels = bytearray(width * height * 3)
    random.seed(42)

    # Generate mountain heights
    mountains = []
    for x in range(width):
        h = 0.3 + 0.15 * math.sin(x * 0.02) + 0.1 * math.sin(x * 0.05) + 0.05 * math.sin(x * 0.13)
        mountains.append(h)

    for y in range(height):
        vy = y / height
        for x in range(width):
            vx = x / width
            mountain_line = mountains[x]

            if vy < 0.15:
                # Sky - gradient from deep blue to orange
                t = vy / 0.15
                r, g, b = lerp_color((25, 25, 80), (255, 140, 50), t)
            elif vy < mountain_line:
                # Sky lower
                t = (vy - 0.15) / max(mountain_line - 0.15, 0.01)
                r, g, b = lerp_color((255, 140, 50), (255, 200, 100), t)
            elif vy < mountain_line + 0.02:
                # Mountain peak (snow)
                r, g, b = 220, 220, 230
            elif vy < 0.55:
                # Mountain body
                t = (vy - mountain_line) / 0.25
                r, g, b = lerp_color((80, 90, 70), (40, 60, 35), t)
            elif vy < 0.7:
                # Water
                t = (vy - 0.55) / 0.15
                wave = math.sin(x * 0.1 + y * 0.3) * 10
                r = int(20 + 30 * t + wave)
                g = int(60 + 40 * t + wave)
                b = int(120 + 30 * t)
            else:
                # Beach/ground
                t = (vy - 0.7) / 0.3
                r, g, b = lerp_color((180, 160, 100), (140, 120, 70), t)

            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))

            idx = (y * width + x) * 3
            pixels[idx] = r
            pixels[idx+1] = g
            pixels[idx+2] = b
    return make_png(width, height, pixels)


def city_image(width, height):
    """Create a city skyline scene."""
    pixels = bytearray(width * height * 3)
    random.seed(99)

    # Building heights and widths
    buildings = []
    x = 0
    while x < width:
        bw = random.randint(30, 80)
        bh = random.uniform(0.3, 0.75)
        buildings.append((x, bw, bh))
        x += bw + random.randint(2, 10)

    for y in range(height):
        vy = y / height
        for x in range(width):
            # Sky gradient (dusk)
            if vy < 0.25:
                t = vy / 0.25
                r, g, b = lerp_color((10, 10, 40), (60, 30, 80), t)
            else:
                t = (vy - 0.25) / 0.75
                r, g, b = lerp_color((60, 30, 80), (180, 80, 40), min(t * 2, 1.0))

            # Draw buildings
            for bx, bw, bh in buildings:
                if bx <= x < bx + bw and vy > (1 - bh):
                    # Building color (dark with windows)
                    r, g, b = 30, 35, 45
                    # Windows
                    wx = (x - bx) % 12
                    wy = int((vy - (1 - bh)) * height) % 16
                    if 2 <= wx <= 6 and 3 <= wy <= 9:
                        if random.random() > 0.3:
                            r, g, b = 255, 230, 150  # Lit window
                        else:
                            r, g, b = 40, 45, 55  # Dark window
                    break

            idx = (y * width + x) * 3
            pixels[idx] = max(0, min(255, r))
            pixels[idx+1] = max(0, min(255, g))
            pixels[idx+2] = max(0, min(255, b))

    return make_png(width, height, pixels)


def product_image(width, height):
    """Create a product-style image with centered object."""
    pixels = bytearray(width * height * 3)
    cx, cy = width // 2, height // 2

    for y in range(height):
        for x in range(width):
            # Soft white/gray background with radial gradient
            dx = (x - cx) / (width / 2)
            dy = (y - cy) / (height / 2)
            dist = math.sqrt(dx*dx + dy*dy)

            bg = int(245 - dist * 30)
            r, g, b = bg, bg, bg

            # Draw a colored sphere (product stand-in)
            sphere_r = min(width, height) * 0.25
            sdx = x - cx
            sdy = y - cy
            sdist = math.sqrt(sdx*sdx + sdy*sdy)

            if sdist < sphere_r:
                # Sphere with lighting
                t = sdist / sphere_r
                nx = sdx / sphere_r
                ny = sdy / sphere_r
                light = max(0, -nx * 0.3 - ny * 0.5 + 0.8)
                r = int(min(255, 40 + 180 * light))
                g = int(min(255, 80 + 120 * light))
                b = int(min(255, 200 + 55 * light))

            # Shadow below sphere
            shadow_cy = cy + int(sphere_r * 0.9)
            shadow_dx = (x - cx) / (sphere_r * 1.5)
            shadow_dy = (y - shadow_cy) / (sphere_r * 0.2)
            shadow_dist = math.sqrt(shadow_dx*shadow_dx + shadow_dy*shadow_dy)
            if shadow_dist < 1.0 and y > cy + sphere_r * 0.7:
                alpha = (1 - shadow_dist) * 0.3
                r = int(r * (1 - alpha))
                g = int(g * (1 - alpha))
                b = int(b * (1 - alpha))

            idx = (y * width + x) * 3
            pixels[idx] = max(0, min(255, r))
            pixels[idx+1] = max(0, min(255, g))
            pixels[idx+2] = max(0, min(255, b))

    return make_png(width, height, pixels)


def team_image(width, height):
    """Create a meeting/collaboration themed abstract image."""
    pixels = bytearray(width * height * 3)

    # Warm conference room colors
    for y in range(height):
        vy = y / height
        for x in range(width):
            vx = x / width
            # Warm wood-tone gradient background
            r = int(180 - 60 * vy + 20 * math.sin(vx * 3))
            g = int(140 - 50 * vy + 15 * math.sin(vx * 3))
            b = int(100 - 40 * vy + 10 * math.sin(vx * 3))

            # Table (horizontal bar in middle)
            if 0.45 < vy < 0.55:
                r, g, b = 120, 85, 50

            # Abstract people shapes (circles)
            people = [(0.2, 0.35, 35), (0.4, 0.3, 30), (0.6, 0.32, 32), (0.8, 0.35, 35)]
            colors_p = [(66, 133, 244), (219, 68, 55), (244, 180, 0), (15, 157, 88)]
            for i, (px, py, pr) in enumerate(people):
                dx = x - px * width
                dy = y - py * height
                if math.sqrt(dx*dx + dy*dy) < pr:
                    r, g, b = colors_p[i]

            idx = (y * width + x) * 3
            pixels[idx] = max(0, min(255, r))
            pixels[idx+1] = max(0, min(255, g))
            pixels[idx+2] = max(0, min(255, b))

    return make_png(width, height, pixels)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    W, H = 640, 480

    images = {
        "sunset-beach.png": gradient_image(W, H, [
            (255, 80, 20), (255, 160, 50), (255, 200, 80),
            (100, 180, 220), (30, 60, 120)
        ]),
        "mountain-landscape.png": landscape_image(W, H),
        "city-skyline.png": city_image(W, H),
        "product-photo.png": product_image(W, H),
        "team-meeting.png": team_image(W, H),
    }

    for name, data in images.items():
        path = os.path.join(OUTPUT_DIR, name)
        with open(path, "wb") as f:
            f.write(data)
        print(f"Generated {path} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
