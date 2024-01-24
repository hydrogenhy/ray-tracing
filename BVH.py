import numpy as np


class BVHNode:
    def __init__(self, bbox, left, right, polygons):
        self.bbox = bbox  # [2, 3] array
        self.left = left
        self.right = right
        self.polygons = polygons

    def max_axis(self):
        x = self.bbox[1][0] - self.bbox[0][0]
        y = self.bbox[1][1] - self.bbox[0][1]
        z = self.bbox[1][2] - self.bbox[0][2]
        if x >= y and x >= z:
            return 0
        elif y >= x and y >= z:
            return 1
        return 2


def data_prep(num_t, position):
    triangle = []
    for i in range(num_t):
        # t = position[i * 3: (i + 1) * 3]
        # min_values = np.min(t, axis=0)
        # max_values = np.max(t, axis=0)
        box = []
        box.extend(position[i * 3])
        box.extend(position[i * 3 + 1])
        box.extend(position[i * 3 + 2])
        box.append(i)
        triangle.append(box)
    # print(position)
    # print(triangle)
    return triangle  # a triangle: (minx, miny, minz, maxx, maxy, maxz, trianID)


def devide(bigbox, triangle):
    global index0
    global BVHTree
    # print(bigbox.polygons)
    if len(bigbox.polygons) <= 4:
        bigbox.left = -1
        bigbox.right = -1
        return
    triangle = np.array(triangle)
    axis = bigbox.max_axis()
    triangles = triangle[np.array(bigbox.polygons, int)]
    triangles = sorted(triangles, key=lambda x: (x[axis] + x[axis + 3] + x[axis + 6]) / 3)
    trian1 = triangles[0:len(bigbox.polygons) // 2]
    trian1 = np.array(trian1)
    trian2 = triangles[len(bigbox.polygons) // 2:]
    trian2 = np.array(trian2)
    bbox1 = np.zeros((2, 3))
    bbox1[0][0] = min([min(trian1[:, 0]), min(trian1[:, 3]), min(trian1[:, 6])])
    bbox1[0][1] = min([min(trian1[:, 1]), min(trian1[:, 4]), min(trian1[:, 7])])
    bbox1[0][2] = min([min(trian1[:, 2]), min(trian1[:, 5]), min(trian1[:, 8])])
    bbox1[1][0] = max([max(trian1[:, 0]), max(trian1[:, 3]), max(trian1[:, 6])])
    bbox1[1][1] = max([max(trian1[:, 1]), max(trian1[:, 4]), max(trian1[:, 7])])
    bbox1[1][2] = max([max(trian1[:, 2]), max(trian1[:, 5]), max(trian1[:, 8])])
    index0 += 1
    left = BVHNode(bbox1, None, None, trian1[:, -1])
    BVHTree.append(left)
    bigbox.left = index0
    bbox2 = np.zeros((2, 3))
    bbox2[0][0] = min([min(trian2[:, 0]), min(trian2[:, 3]), min(trian2[:, 6])])
    bbox2[0][1] = min([min(trian2[:, 1]), min(trian2[:, 4]), min(trian2[:, 7])])
    bbox2[0][2] = min([min(trian2[:, 2]), min(trian2[:, 5]), min(trian2[:, 8])])
    bbox2[1][0] = max([max(trian2[:, 0]), max(trian2[:, 3]), max(trian2[:, 6])])
    bbox2[1][1] = max([max(trian2[:, 1]), max(trian2[:, 4]), max(trian2[:, 7])])
    bbox2[1][2] = max([max(trian2[:, 2]), max(trian2[:, 5]), max(trian2[:, 8])])
    index0 += 1
    bigbox.right = index0
    right = BVHNode(bbox2, None, None, trian2[:, -1])
    BVHTree.append(right)

    devide(left, triangle)
    devide(right, triangle)


def creat_BVH(num_t, triangle):
    print('共有三角形数目：', len(triangle))
    global index0
    global BVHTree
    triangle = np.array(triangle)
    bbox = np.zeros((2, 3))
    bbox[0][0] = min([min(triangle[:, 0]), min(triangle[:, 3]), min(triangle[:, 6])])
    bbox[0][1] = min([min(triangle[:, 1]), min(triangle[:, 4]), min(triangle[:, 7])])
    bbox[0][2] = min([min(triangle[:, 2]), min(triangle[:, 5]), min(triangle[:, 8])])
    bbox[1][0] = max([max(triangle[:, 0]), max(triangle[:, 3]), max(triangle[:, 6])])
    bbox[1][1] = max([max(triangle[:, 1]), max(triangle[:, 4]), max(triangle[:, 7])])
    bbox[1][2] = max([max(triangle[:, 2]), max(triangle[:, 5]), max(triangle[:, 8])])
    root = BVHNode(bbox, 0, 0, np.arange(0, num_t))
    print('Creating BVHTree')
    BVHTree.append(root)
    devide(root, triangle)
    print('Finish!')
    child_info = []  # left, right, none
    box1 = []  # min axis
    box2 = []  # max axis
    samples = []  # leaf -> triangle
    for x in BVHTree:
        child_info.append([x.left, x.right, 0])
        box1.append(list(x.bbox[0, :]))
        box2.append(list(x.bbox[1, :]))
        if x.left == -1:
            tmp_polygons = []
            tmp_polygons.extend(list(x.polygons))
            tmp_polygons.extend([-1, -1, -1])
            samples.append(tmp_polygons[0: 4])
        else:
            samples.append([-1, -1, -1, -1])
    print('VBHTree node num:', index0)
    # print(child_info, '\n', box1, '\n', box2, '\n', samples)
    return np.array(child_info, np.float32), np.array(box1, np.float32), \
           np.array(box2, np.float32), np.array(samples, np.float32)


index0 = 0
BVHTree = []
# data = [
#         [0, 0, 0], [1, 0, 0], [0, 1, 0],
#         [1, 0, 0], [1, 1, 0], [0, 1, 0],
#         [0, 0, 0], [0, 0, 1], [1, 0, 0],
#         [1, 0, 0], [0, 0, 1], [1, 0, 1]
#     ]
# child_info, box1, box2, samples = creat_BVH(4, data_prep(4, data))
# print(child_info, '\n', box1, '\n', box2, '\n', samples)
