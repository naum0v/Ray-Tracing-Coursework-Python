import math
from typing import List

class Vec3:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z

    def __getitem__(self, i):
        if i == 0: return self.x
        if i == 1: return self.y
        if i == 2: return self.z
        raise IndexError("Index out of range")

def save_ppm(filename: str, width: int, height: int, framebuffer: List[Vec3]):
    with open(filename, 'wb') as f:
        f.write(f"P6\n{width} {height}\n255\n".encode())
        for color in framebuffer:
            max_val = max(1.0, max(color[0], max(color[1], color[2])))
            r = int(255 * color[0] / max_val)
            g = int(255 * color[1] / max_val)
            b = int(255 * color[2] / max_val)
            f.write(bytes([r, g, b]))

def main():
    width = 1024
    height = 768
    framebuffer = [Vec3() for _ in range(width * height)]

    for j in range(height):
        for i in range(width):
            r = j / float(height)
            g = i / float(width)
            b = 0.0
            framebuffer[i + j * width] = Vec3(r, g, b)

    save_ppm("output_step1.ppm", width, height, framebuffer)

if __name__ == "__main__":
    main()