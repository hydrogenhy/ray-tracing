import numpy as np
import math


def rotate_point_around_x(point, angle):
    """
    旋转三维点绕 x 轴的函数
    """
    x, y, z = point
    radian_angle = math.radians(angle)

    new_y = y * math.cos(radian_angle) - z * math.sin(radian_angle)
    new_z = y * math.sin(radian_angle) + z * math.cos(radian_angle)

    return [x, new_y, new_z]


def rotate_points_around_x(point_list, angle):
    """
    旋转多个三维点绕 x 轴的函数
    """
    return [rotate_point_around_x(point, angle) for point in point_list]


def rotate_point_around_z(point, angle):
    """
    旋转三维点绕 z 轴的函数
    """
    x, y, z = point
    radian_angle = math.radians(angle)

    new_x = x * math.cos(radian_angle) - y * math.sin(radian_angle)
    new_y = x * math.sin(radian_angle) + y * math.cos(radian_angle)

    return [new_x, new_y, z]


def rotate_points_around_z(point_list, angle):
    """
    旋转多个三维点绕 z 轴的函数
    """
    return [rotate_point_around_z(point, angle) for point in point_list]


def load_obj(file_path, scale):
    vertices = []
    faces = []

    with open(file_path, 'r') as f:
        for line in f:
            tokens = line.split()
            if len(tokens) == 0:
                continue

            if tokens[0] == 'v':
                # 顶点数据
                vertex = list(map(float, tokens[1:]))
                vertices.append(vertex)
            elif tokens[0] == 'f':
                # 面数据
                face = [int(v.split('/')[0]) for v in tokens[1:]]
                faces.append(face)

    vertices = rotate_points_around_x(vertices, 90)
    vertices = rotate_points_around_z(vertices, 90)
    vertices = [[x * scale for x in row] for row in vertices]
    vertices = [[x + 0.2, y + 0.4, z - 3] for x, y, z in vertices]
    trians = []
    for x in faces:
        trians.append(vertices[x[0] - 1])
        trians.append(vertices[x[1] - 1])
        trians.append(vertices[x[2] - 1])
    # color = [[1.0, 0.5, 0.0]] * len(faces) * 3
    color = [[1.0, 0.5, 0.0]] * len(faces) * 3
    print('导入模型的三角形数量为: ', len(faces))

    return trians, color, len(faces)

# points = load_obj('box.obj')
# print(points)
