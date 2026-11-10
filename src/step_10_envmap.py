import math
import struct
import random
from PIL import Image
import os


# ============================================================================
# Классы для представления векторной математики и структур данных
# ============================================================================

class Vec3:
    """Класс для представления 3D вектора"""

    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z

    def __getitem__(self, i):
        """Доступ к компонентам по индексу [0,1,2]"""
        if i == 0: return self.x
        if i == 1: return self.y
        if i == 2: return self.z
        raise IndexError("Index out of range")

    def __mul__(self, other):
        """Умножение вектора на скаляр или скалярное произведение"""
        if isinstance(other, (int, float)):
            return Vec3(self.x * other, self.y * other, self.z * other)
        # Скалярное произведение
        return self.x * other.x + self.y * other.y + self.z * other.z

    def __add__(self, other):
        """Сложение векторов"""
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        """Вычитание векторов"""
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __neg__(self):
        """Отрицание вектора"""
        return Vec3(-self.x, -self.y, -self.z)

    def norm(self):
        """Длина (модуль) вектора"""
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def normalized(self):
        """Нормализация вектора (приведение к длине 1)"""
        length = self.norm()
        if length > 0:
            return self * (1.0 / length)
        return Vec3()

    def __str__(self):
        return f"({self.x}, {self.y}, {self.z})"


def cross(v1, v2):
    """Векторное произведение двух векторов"""
    return Vec3(
        v1.y * v2.z - v1.z * v2.y,
        v1.z * v2.x - v1.x * v2.z,
        v1.x * v2.y - v1.y * v2.x
    )


# ============================================================================
# Структуры материалов и объектов сцены
# ============================================================================

class Material:
    """Структура материала определяет оптические свойства поверхности"""

    def __init__(self, refractive_index=1.0, albedo=None, diffuse_color=None, specular_exponent=0.0):
        self.refractive_index = refractive_index
        self.albedo = albedo if albedo is not None else [2.0, 0.0, 0.0, 0.0]
        self.diffuse_color = diffuse_color if diffuse_color is not None else Vec3(0.0, 0.0, 0.0)
        self.specular_exponent = specular_exponent


class Sphere:
    """Структура сферы: центр, радиус и материал"""

    def __init__(self, center, radius, material):
        self.center = center
        self.radius = radius
        self.material = material


# ============================================================================
# Функции для работы с фоновой картой (envmap)
# ============================================================================

class EnvMap:
    """Класс для работы с фоновой картой (environment map)"""

    def __init__(self, filename=None):
        self.width = 0
        self.height = 0
        self.data = []

        if filename and os.path.exists(filename):
            if self.load_from_file(filename):
                print(f"Фоновая карта загружена из {filename}")
            else:
                print(f"Не удалось загрузить фоновую карту из {filename}")
                # В случае ошибки загрузки используем стандартный фон
                self.create_default_background()
        else:
            print(f"Файл фоновой карты '{filename}' не найден")
            self.create_default_background()

    def create_default_background(self):
        """Создает простой одноцветный фон"""
        self.width = 1
        self.height = 1
        # Используем стандартный голубой цвет как в предыдущих шагах
        self.data = [Vec3(0.2, 0.7, 0.8)]

    def load_from_file(self, filename):
        """Загружает фоновую карту из файла с помощью PIL"""
        try:
            # Открываем изображение с помощью PIL
            img = Image.open(filename)

            # Конвертируем в RGB, если изображение в другом формате
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Получаем размеры изображения
            self.width, self.height = img.size

            # Загружаем пиксели
            pixels = list(img.getdata())

            # Преобразуем пиксели в объекты Vec3
            self.data = []
            for pixel in pixels:
                # PIL возвращает кортеж (R, G, B) с значениями от 0 до 255
                r, g, b = pixel
                # Преобразуем в диапазон [0, 1]
                color = Vec3(r / 255.0, g / 255.0, b / 255.0)
                self.data.append(color)

            img.close()
            print(f"Успешно загружена фоновая карта: {filename}, размер: {self.width}x{self.height}")
            return True

        except Exception as e:
            print(f"Ошибка при загрузке фоновой карты {filename}: {e}")
            return False

    def get_color(self, dir):
        """Получает цвет из фоновой карты по направлению"""
        # Если размер карты 1x1, возвращаем единственный цвет
        if self.width == 1 and self.height == 1:
            return self.data[0]

        # Нормализуем направление
        dir = dir.normalized()

        # Преобразуем направление в UV-координаты
        # atan2 возвращает угол в диапазоне [-π, π]
        u = 0.5 + math.atan2(dir.z, dir.x) / (2 * math.pi)
        v = 0.5 - math.asin(dir.y) / math.pi

        # Преобразуем UV в пиксельные координаты
        i = int(u * self.width)
        j = int(v * self.height)

        # Ограничиваем индексы
        i = max(0, min(self.width - 1, i))
        j = max(0, min(self.height - 1, j))

        return self.data[i + j * self.width]


# ============================================================================
# Предопределенные материалы с реалистичными параметрами
# ============================================================================

ivory = Material(1.0, [0.9, 0.5, 0.1, 0.0], Vec3(0.4, 0.4, 0.3), 50.0)
glass = Material(1.5, [0.0, 0.9, 0.1, 0.8], Vec3(0.6, 0.7, 0.8), 125.0)
red_rubber = Material(1.0, [1.4, 0.3, 0.0, 0.0], Vec3(0.3, 0.1, 0.1), 10.0)
mirror = Material(1.0, [0.0, 16.0, 0.8, 0.0], Vec3(1.0, 1.0, 1.0), 1425.0)

# Сцена: массив сфер с разными материалами и положениями
spheres = [
    Sphere(Vec3(-3, 0, -16), 2.0, ivory),
    Sphere(Vec3(-1.0, -1.5, -12), 2.0, glass),
    Sphere(Vec3(1.5, -0.5, -18), 3.0, red_rubber),
    Sphere(Vec3(7, 5, -18), 4.0, mirror)
]

# Источники света в сцене (точечные источники)
lights = [
    Vec3(-20, 20, 20),
    Vec3(30, 50, -25),
    Vec3(30, 20, 30)
]


# ============================================================================
# Оптические вычисления
# ============================================================================

def reflect(I, N):
    """
    Вычисление отраженного луча по закону отражения
    I - падающий луч (направление от камеры к точке)
    N - нормаль к поверхности в точке падения
    return отраженный луч
    """
    return I - N * 2.0 * (I * N)


def refract(I, N, eta_t, eta_i=1.0):
    """
    Вычисление преломленного луча по закону Снеллиуса
    I - падающий луч
    N - нормаль к поверхности
    eta_t - показатель преломления целевой среды
    eta_i - показатель преломления исходной среды
    return преломленный луч или (1,0,0) при полном внутреннего отражения
    """
    cosi = -max(-1.0, min(1.0, I * N))

    if cosi < 0:
        return refract(I, -N, eta_i, eta_t)

    eta = eta_i / eta_t
    k = 1 - eta * eta * (1 - cosi * cosi)

    if k < 0:
        return Vec3(1.0, 0.0, 0.0)
    else:
        return I * eta + N * (eta * cosi - math.sqrt(k))


# ============================================================================
# Пересечения лучей с объектами
# ============================================================================

def ray_sphere_intersect(orig, dir, sphere):
    """
    Проверка пересечения луча со сферой
    orig - начало луча
    dir - направление луча
    sphere - сфера для проверки
    return [найдено ли пересечение, расстояние до пересечения]
    """
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
    """
    Поиск ближайшего пересечения луча со всей сценой
    orig - начало луча
    dir - направление луча
    return [есть ли пересечение, точка пересечения, нормаль, материал]
    """
    pt = Vec3()
    N = Vec3()
    material = Material()

    nearest_dist = 1e10

    # Проверка пересечения с полом (плоскость y = -4)
    if abs(dir.y) > 0.001:
        d = -(orig.y + 4) / dir.y
        p = orig + dir * d

        if d > 0.001 and d < nearest_dist and abs(p.x) < 10 and p.z < -10 and p.z > -30:
            nearest_dist = d
            pt = p
            N = Vec3(0, 1, 0)

            # Создаем шахматный узор на полу
            if (int(0.5 * p.x + 1000) + int(0.5 * p.z)) & 1:
                material.diffuse_color = Vec3(0.3, 0.3, 0.3)  # Темные клетки
            else:
                material.diffuse_color = Vec3(0.3, 0.2, 0.1)  # Светлые клетки

    # Проверка пересечения со всеми сферами
    for sphere in spheres:
        intersection, d = ray_sphere_intersect(orig, dir, sphere)
        if not intersection or d > nearest_dist:
            continue

        nearest_dist = d
        pt = orig + dir * nearest_dist
        N = (pt - sphere.center).normalized()
        material = sphere.material

    return nearest_dist < 1000, pt, N, material


# ============================================================================
# Основной алгоритм трассировки лучей
# ============================================================================

def cast_ray(orig, dir, depth=0):
    """
    Рекурсивная функция трассировки луча
    orig - начало луча
    dir - направление луча
    depth - текущая глубина рекурсии
    return цвет в направлении луча
    """
    hit, point, N, material = scene_intersect(orig, dir)

    # Если нет пересечения или превышена глубина рекурсии - возвращаем цвет из фоновой карты
    if depth > 4 or not hit:
        return envmap.get_color(dir)

    # Вычисляем направления отраженного и преломленного лучей
    reflect_dir = reflect(dir, N).normalized()
    refract_dir = refract(dir, N, material.refractive_index).normalized()

    # Смещаем точки испускания вторичных лучей для избежания самопересечения
    reflect_orig = point + N * 0.001
    refract_orig = point - N * 0.001 if refract_dir * N < 0 else point + N * 0.001

    # Рекурсивно трассируем отраженный и преломленный лучи
    reflect_color = cast_ray(reflect_orig, reflect_dir, depth + 1)
    refract_color = cast_ray(refract_orig, refract_dir, depth + 1)

    # Расчет освещения (диффузного и зеркального)
    diffuse_light_intensity = 0.0
    specular_light_intensity = 0.0

    # Для каждого источника света
    for light in lights:
        light_dir = (light - point).normalized()

        # Проверка нахождения в тени: пускаем луч к свету
        shadow_hit, shadow_pt, trash_nrm, trash_mat = scene_intersect(point, light_dir)

        # Если есть пересечение ближе чем источник - точка в тени
        if shadow_hit and (shadow_pt - point).norm() < (light - point).norm():
            continue

        # Диффузная составляющая (по Ламберту)
        diffuse_light_intensity += max(0.0, light_dir * N)

        # Зеркальная составляющая (блики по Фонгу)
        specular_light_intensity += math.pow(
            max(0.0, -reflect(-light_dir, N) * dir),
            material.specular_exponent
        )

    # Комбинируем все компоненты освещения с коэффициентами albedo
    diffuse_component = material.diffuse_color * diffuse_light_intensity * material.albedo[0]
    specular_component = Vec3(1.0, 1.0, 1.0) * specular_light_intensity * material.albedo[1]
    reflection_component = reflect_color * material.albedo[2]
    refraction_component = refract_color * material.albedo[3]

    return diffuse_component + specular_component + reflection_component + refraction_component


# ============================================================================
# Основная функция рендеринга
# ============================================================================

def save_ppm(filename, width, height, framebuffer):
    """Сохранение изображения в PPM формате"""
    with open(filename, 'wb') as f:
        # Заголовок PPM
        f.write(f"P6\n{width} {height}\n255\n".encode())

        # Данные пикселей
        for color in framebuffer:
            # Находим максимальную компоненту для нормализации
            max_val = max(1.0, max(color[0], max(color[1], color[2])))

            # Преобразование float цветов в байты [0,255]
            r = int(255 * color[0] / max_val)
            g = int(255 * color[1] / max_val)
            b = int(255 * color[2] / max_val)

            f.write(bytes([r, g, b]))


def main():
    """Основная функция рендеринга"""
    width = 1024
    height = 768
    fov = 1.05  # 60 градусов поля зрения в радианах

    # Загружаем фоновую карту
    global envmap
    envmap = EnvMap("envmap.jpg")

    # Буфер для хранения цветов всех пикселей
    framebuffer = [Vec3() for _ in range(width * height)]

    print("Начало рендеринга с фоновой картой...")

    # Основной цикл рендеринга
    for pix in range(width * height):
        # Преобразование линейного индекса в координаты (x,y)
        x = pix % width
        y = pix // width

        dir_x = (x + 0.5) - width / 2.0
        dir_y = -(y + 0.5) + height / 2.0  # Переворачиваем Y координату
        dir_z = -height / (2.0 * math.tan(fov / 2.0))

        # Трассировка луча из начала координат через текущий пиксель
        ray_dir = Vec3(dir_x, dir_y, dir_z).normalized()
        framebuffer[pix] = cast_ray(Vec3(0, 0, 0), ray_dir)

        # Прогресс
        if pix % (width * 10) == 0:
            progress = (pix / (width * height)) * 100
            print(f"Прогресс: {progress:.1f}%")

    # Сохранение результата
    save_ppm("output_envmap.ppm", width, height, framebuffer)
    print("Рендеринг завершен. Результат сохранен в output_envmap.ppm")
    print("Фон теперь использует сферическую карту вместо постоянного цвета")


if __name__ == "__main__":
    # Глобальная фоновая карта
    envmap = None
    main()