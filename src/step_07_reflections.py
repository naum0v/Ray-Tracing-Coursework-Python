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

    def __neg__(self):
        return Vec3(-self.x, -self.y, -self.z)

    def norm(self):
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def normalized(self):
        length = self.norm()
        if length > 0:
            return self * (1.0 / length)
        return Vec3()

class Material:
    def __init__(self, refractive_index=1.0, albedo=None, diffuse_color=None, specular_exponent=0.0):
        self.refractive_index = refractive_index
        self.albedo = albedo if albedo is not None else [2.0, 0.0, 0.0, 0.0]
        self.diffuse_color = diffuse_color if diffuse_color is not None else Vec3(0.0, 0.0, 0.0)
        self.specular_exponent = specular_exponent

class Sphere:
    def __init__(self, center, radius, material):
        self.center = center
        self.radius = radius
        self.material = material

ivory = Material(1.0, [0.9, 0.5, 0.1, 0.0], Vec3(0.4, 0.4, 0.3), 50.0)
glass = Material(1.5, [0.0, 0.9, 0.1, 0.8], Vec3(0.6, 0.7, 0.8), 125.0)
red_rubber = Material(1.0, [1.4, 0.3, 0.0, 0.0], Vec3(0.3, 0.1, 0.1), 10.0)
mirror = Material(1.0, [0.0, 16.0, 0.8, 0.0], Vec3(1.0, 1.0, 1.0), 1425.0)

spheres = [
    Sphere(Vec3(-3, 0, -16), 2.0, ivory),      # Глянцевый шар слева
    Sphere(Vec3(-1.0, -1.5, -12), 2.0, glass), # Стеклянный шар по центру
    Sphere(Vec3(1.5, -0.5, -18), 3.0, red_rubber), # Матовый шар справа
    Sphere(Vec3(7, 5, -18), 4.0, mirror)       # Зеркальный шар справа вверху
]

lights = [
    Vec3(-20, 20, 20),
    Vec3(30, 50, -25),
    Vec3(30, 20, 30)
]

def reflect(I, N):
    return I - N * 2.0 * (I * N)

def refract(I, N, eta_t, eta_i=1.0):
    cosi = -max(-1.0, min(1.0, I * N))

    if cosi < 0:
        return refract(I, -N, eta_i, eta_t)

    eta = eta_i / eta_t
    k = 1 - eta * eta * (1 - cosi * cosi)

    if k < 0:
        return Vec3(1.0, 0.0, 0.0)
    else:
        return I * eta + N * (eta * cosi - math.sqrt(k))

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
    material = Material()
    nearest_dist = 1e10

    for sphere in spheres:
        intersection, d = ray_sphere_intersect(orig, dir, sphere)
        if not intersection or d > nearest_dist:
            continue

        nearest_dist = d
        pt = orig + dir * nearest_dist
        N = (pt - sphere.center).normalized()
        material = sphere.material

    return nearest_dist < 1000, pt, N, material

def cast_ray(orig, dir, depth=0):
    hit, point, N, material = scene_intersect(orig, dir)

    if depth > 4 or not hit:
        return Vec3(0.2, 0.7, 0.8)

    # Три ключевые строки для отражений
    reflect_dir = reflect(dir, N).normalized()
    reflect_orig = point + N * 0.001
    reflect_color = cast_ray(reflect_orig, reflect_dir, depth + 1)

    # Для преломлений (пока не используется активно)
    refract_dir = refract(dir, N, material.refractive_index).normalized()
    refract_orig = point - N * 0.001
    refract_color = cast_ray(refract_orig, refract_dir, depth + 1)

    diffuse_light_intensity = 0.0
    specular_light_intensity = 0.0

    for light in lights:
        light_dir = (light - point).normalized()

        shadow_hit, shadow_pt, trash_nrm, trash_mat = scene_intersect(point, light_dir)

        if shadow_hit and (shadow_pt - point).norm() < (light - point).norm():
            continue

        diffuse_light_intensity += max(0.0, light_dir * N)

        specular_light_intensity += math.pow(
            max(0.0, -reflect(-light_dir, N) * dir),
            material.specular_exponent
        )

    diffuse_component = material.diffuse_color * diffuse_light_intensity * material.albedo[0]
    specular_component = Vec3(1.0, 1.0, 1.0) * specular_light_intensity * material.albedo[1]
    reflection_component = reflect_color * material.albedo[2]
    refraction_component = refract_color * material.albedo[3]

    return diffuse_component + specular_component + reflection_component + refraction_component

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

    print("Начало рендеринга с отражениями...")

    for pix in range(width * height):
        x = pix % width
        y = pix // width

        dir_x = (x + 0.5) - width / 2.0
        dir_y = -(y + 0.5) + height / 2.0
        dir_z = -height / (2.0 * math.tan(fov / 2.0))

        ray_dir = Vec3(dir_x, dir_y, dir_z).normalized()
        framebuffer[pix] = cast_ray(Vec3(0, 0, 0), ray_dir)

    save_ppm("output_step7.ppm", width, height, framebuffer)
    print("Изображение сохранено в output_step7.ppm")

if __name__ == "__main__":
    main()