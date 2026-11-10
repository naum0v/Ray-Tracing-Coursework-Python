import math

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

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return Vec3(self.x * other, self.y * other, self.z * other)
        return self.x * other.x + self.y * other.y + self.z * other.z

    def __add__(self, other):
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def norm(self):
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def normalized(self):
        length = self.norm()
        if length > 0:
            return self * (1.0 / length)
        return Vec3()

class Sphere:
    def __init__(self, center, radius, color):
        self.center = center
        self.radius = radius
        self.color = color

spheres = [
    Sphere(Vec3(-3, 0, -16), 2.0, Vec3(0.4, 0.4, 0.3)),
    Sphere(Vec3(-1.0, -1.5, -12), 2.0, Vec3(0.6, 0.7, 0.8)),
    Sphere(Vec3(1.5, -0.5, -18), 3.0, Vec3(0.3, 0.1, 0.1)),
    Sphere(Vec3(7, 5, -18), 4.0, Vec3(1.0, 1.0, 1.0))
]

def ray_sphere_intersect(orig, dir, sphere):
    L = sphere.center - orig
    tca = L * dir
    d2 = (L * L) - tca * tca

    if d2 > sphere.radius * sphere.radius:
        return False, 0.0

    thc = math.sqrt(sphere.radius * sphere.radius - d2)
    t0 = tca - thc
    t1 = tca + thc

    if t0 > 0.001:
        return True, t0
    if t1 > 0.001:
        return True, t1

    return False, 0.0

def scene_intersect(orig, dir):
    pt = Vec3()
    N = Vec3()
    color = Vec3()
    nearest_dist = 1e10

    for sphere in spheres:
        intersection, d = ray_sphere_intersect(orig, dir, sphere)
        if not intersection or d > nearest_dist:
            continue

        nearest_dist = d
        pt = orig + dir * nearest_dist
        N = (pt - sphere.center).normalized()
        color = sphere.color

    return nearest_dist < 1000, pt, N, color

def cast_ray(orig, dir):
    hit, point, N, color = scene_intersect(orig, dir)

    if not hit:
        return Vec3(0.2, 0.7, 0.8)

    return color

def save_ppm(filename, width, height, framebuffer):
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
    fov = 1.05

    framebuffer = [Vec3() for _ in range(width * height)]

    for pix in range(width * height):
        x = pix % width
        y = pix // width

        dir_x = (x + 0.5) - width / 2.0
        dir_y = -(y + 0.5) + height / 2.0
        dir_z = -height / (2.0 * math.tan(fov / 2.0))

        ray_dir = Vec3(dir_x, dir_y, dir_z).normalized()
        framebuffer[pix] = cast_ray(Vec3(0, 0, 0), ray_dir)

    save_ppm("output_step3.ppm", width, height, framebuffer)
    print("Изображение сохранено в output_step3.ppm")

if __name__ == "__main__":
    main()