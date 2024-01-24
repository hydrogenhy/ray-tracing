from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GL import shaders
from PIL import Image
from PIL import ImageOps
import glm
from BVH import *
from load_model import *

def load_shader(filename, encoding='utf-8'):
    with open(filename, 'r', encoding=encoding) as file:
        return file.read()

VERTEX_SHADER = load_shader('whitted_style.vs')

FRAGMENT_SHADER = load_shader('whitted_style.fs')

shaderProgram = None
VAO = None
numbers = 30
NumVertices = numbers * (numbers) * 2 * 3
NumVertices = 1 * NumVertices + 36 + 6 - 6


positions = []
normal = []
vPositions = [[] for i in range(NumVertices)]
vColor = [[] for i in range(NumVertices)]
vNormal = [[] for i in range(NumVertices)]
index = 0

light = glm.vec3(0, 0, 3.95)
viewPos = glm.vec3(3.9, 0.0, 0.0)

window_x = 660 #640
window_y = 500 #480

def node(x, y, z, r):
    if numbers == 0:
        return
    for phi in np.arange(0.0, 1.0 * np.pi + 1e-6, 1.0 * np.pi / numbers):
        for theta in np.arange(0.0, 2.0 * np.pi + 1e-6, 2.0 * np.pi / numbers):
            positions.append([r * np.sin(phi) * np.cos(theta) + x,
                              r * np.sin(phi) * np.sin(theta) + y,
                              r * np.cos(phi) + z])
            normal.append([np.sin(phi) * np.cos(theta),
                           np.sin(phi) * np.sin(theta),
                           np.cos(phi)])
    # print(positions)
    # print(f'共有{len(positions)}个点')


def quad(a, b, c, d, colors):
    global index
    norm = np.cross(np.array(positions[c]) - np.array(positions[a]), np.array(positions[b]) - np.array(positions[a]))
    if np.linalg.norm(norm) == 0:
        norm = np.array(positions[a]) / np.linalg.norm(positions[a])
    else:
        norm /= np.linalg.norm(norm)
    vNormal[index], vPositions[index], vColor[index], index = norm, positions[a], colors, index + 1
    vNormal[index], vPositions[index], vColor[index], index = norm, positions[b], colors, index + 1
    vNormal[index], vPositions[index], vColor[index], index = norm, positions[c], colors, index + 1
    norm = np.cross(np.array(positions[d]) - np.array(positions[a]), np.array(positions[c]) - np.array(positions[a]))
    if np.linalg.norm(norm) == 0:
        norm = np.array(positions[a]) / np.linalg.norm(positions[a])
    else:
        norm /= np.linalg.norm(norm)
    vNormal[index], vPositions[index], vColor[index], index = norm, positions[a], colors, index + 1
    vNormal[index], vPositions[index], vColor[index], index = norm, positions[c], colors, index + 1
    vNormal[index], vPositions[index], vColor[index], index = norm, positions[d], colors, index + 1


def quad_cube(a, b, c, d, normals, colors):
    global index
    cube_positions = [
        [-4, -4, 4], [-4, 4, 4], [4, 4, 4], [4, -4, 4],
        [-4, -4, -4], [-4, 4, -4], [4, 4, -4], [4, -4, -4],
        [-0.8, -0.8, 3.99], [-0.8, 0.8, 3.99], [0.8, 0.8, 3.99], [0.8, -0.8, 3.99]
    ]
    vNormal[index], vPositions[index], vColor[index], index = normals, cube_positions[a], colors, index + 1
    vNormal[index], vPositions[index], vColor[index], index = normals, cube_positions[b], colors, index + 1
    vNormal[index], vPositions[index], vColor[index], index = normals, cube_positions[c], colors, index + 1
    vNormal[index], vPositions[index], vColor[index], index = normals, cube_positions[a], colors, index + 1
    vNormal[index], vPositions[index], vColor[index], index = normals, cube_positions[c], colors, index + 1
    vNormal[index], vPositions[index], vColor[index], index = normals, cube_positions[d], colors, index + 1


def cube_quad():
    quad_cube(5, 4, 0, 1, [1.0, 0.0, 0.0], [1.0, 1.0, 1.0])  # back [1.0, 0.5, 0.0]
    quad_cube(2, 3, 7, 6, [-1.0, 0.0, 0.0], [1.0, 1.0, 0.0])  # front
    quad_cube(3, 0, 4, 7, [0.0, 1.0, 0.0], [1.0, 0.0, 0.0])  # left
    quad_cube(1, 0, 3, 2, [0.0, 0.0, -1.0], [0.5, 0.5, 0.50])  # up
    quad_cube(6, 5, 1, 2, [0.0, -1.0, 0.0], [0.0, 1.0, 0.0])  # right
    quad_cube(4, 5, 6, 7, [0.0, 0.0, 1], [0.0, 0.8, 1.0])  # bottom
    # quad_cube(9, 8, 11, 10, [0.0, 0.0, -1.0], [1.0, 1.0, 1.0])  # light


def quad_sphere(colors):
    for i in range(numbers):
        for j in range(numbers):
            if j != numbers:
                quad(i * (numbers + 1) + j, i * (numbers + 1) + j + 1, (i + 1) * (numbers + 1) + j + 1,
                     (i + 1) * (numbers + 1) + j, colors)
            else:
                quad(i * (numbers + 1) + j, (i * (numbers + 1)), (i + 1) * (numbers + 1), (i + 1) * (numbers + 1) + j, colors)


def initliaze():
    global VERTEXT_SHADER
    global FRAGMEN_SHADER
    global shaderProgram
    global VAO
    global NumVertices

    vertexshader = shaders.compileShader(VERTEX_SHADER, GL_VERTEX_SHADER)
    fragmentshader = shaders.compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)

    shaderProgram = shaders.compileProgram(vertexshader, fragmentshader)

    screen = [[-10, 100, 100, 1], [-10, 100, -100, 1], [-10, -100, -100, 1],
              [-10, 100, 100, 1], [-10, -100, -100, 1], [-10, -100, 100, 1]]
    screen = np.array(screen, np.float32)
    VAO = glGenVertexArrays(1)
    glBindVertexArray(VAO)
    VBO = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, VBO)
    glBufferData(GL_ARRAY_BUFFER, screen.nbytes, None, GL_STATIC_DRAW)
    glBufferSubData(GL_ARRAY_BUFFER, 0, screen.nbytes, screen)
    glVertexAttribPointer(0, 4, GL_FLOAT, GL_FALSE, 16, None)
    glEnableVertexAttribArray(0)

    model_trian_num = 0
    model_points, model_color, model_trian_num = load_obj('bunny/reconstruction/bun_zipper_res2.ply.obj', scale=13)
    vPositions.extend(model_points)
    vColor.extend(model_color)
    points = np.array(vPositions, np.float32)
    color = np.array(vColor, np.float32)
    normal = np.array(vNormal, np.float32)
    NumVertices = NumVertices // 3  + model_trian_num
    child_info, box1, box2, samples = creat_BVH(NumVertices, data_prep(NumVertices, vPositions))
    # child_info, box1, box2, samples = creat_BVH(model_trian_num, data_prep(model_trian_num, points))

    glActiveTexture(GL_TEXTURE0)
    TBO1 = glGenBuffers(1)
    glBindBuffer(GL_TEXTURE_BUFFER, TBO1)
    glBufferData(GL_TEXTURE_BUFFER, points.nbytes, points, GL_STATIC_DRAW)
    trianglesBuffer = glGenTextures(1)
    glBindTexture(GL_TEXTURE_BUFFER, trianglesBuffer)
    glTexBuffer(GL_TEXTURE_BUFFER, GL_RGB32F, TBO1)

    glActiveTexture(GL_TEXTURE1)
    TBO2 = glGenBuffers(1)
    glBindBuffer(GL_TEXTURE_BUFFER, TBO2)
    glBufferData(GL_TEXTURE_BUFFER, color.nbytes, color, GL_STATIC_DRAW)
    trianglesColor = glGenTextures(1)
    glBindTexture(GL_TEXTURE_BUFFER, trianglesColor)
    glTexBuffer(GL_TEXTURE_BUFFER, GL_RGB32F, TBO2)

    glActiveTexture(GL_TEXTURE2)
    TBO3 = glGenBuffers(1)
    glBindBuffer(GL_TEXTURE_BUFFER, TBO3)
    glBufferData(GL_TEXTURE_BUFFER, normal.nbytes, normal, GL_STATIC_DRAW)
    trianglesNormal = glGenTextures(1)
    glBindTexture(GL_TEXTURE_BUFFER, trianglesNormal)
    glTexBuffer(GL_TEXTURE_BUFFER, GL_RGB32F, TBO3)

    glActiveTexture(GL_TEXTURE3)
    TBO4 = glGenBuffers(1)
    glBindBuffer(GL_TEXTURE_BUFFER, TBO4)
    glBufferData(GL_TEXTURE_BUFFER, child_info.nbytes, child_info, GL_STATIC_DRAW)
    BVHChild = glGenTextures(1)
    glBindTexture(GL_TEXTURE_BUFFER, BVHChild)
    glTexBuffer(GL_TEXTURE_BUFFER, GL_RGB32F, TBO4)

    glActiveTexture(GL_TEXTURE4)
    TBO5 = glGenBuffers(1)
    glBindBuffer(GL_TEXTURE_BUFFER, TBO5)
    glBufferData(GL_TEXTURE_BUFFER, box1.nbytes, box1, GL_STATIC_DRAW)
    Box1 = glGenTextures(1)
    glBindTexture(GL_TEXTURE_BUFFER, Box1)
    glTexBuffer(GL_TEXTURE_BUFFER, GL_RGB32F, TBO5)

    glActiveTexture(GL_TEXTURE5)
    TBO6 = glGenBuffers(1)
    glBindBuffer(GL_TEXTURE_BUFFER, TBO6)
    glBufferData(GL_TEXTURE_BUFFER, box2.nbytes, box2, GL_STATIC_DRAW)
    Box2 = glGenTextures(1)
    glBindTexture(GL_TEXTURE_BUFFER, Box2)
    glTexBuffer(GL_TEXTURE_BUFFER, GL_RGB32F, TBO6)

    glActiveTexture(GL_TEXTURE6)
    TBO7 = glGenBuffers(1)
    glBindBuffer(GL_TEXTURE_BUFFER, TBO7)
    glBufferData(GL_TEXTURE_BUFFER, samples.nbytes, samples, GL_STATIC_DRAW)
    BVHSampler = glGenTextures(1)
    glBindTexture(GL_TEXTURE_BUFFER, BVHSampler)
    glTexBuffer(GL_TEXTURE_BUFFER, GL_RGBA32F, TBO7)


def calc_mvp(width, height):
    proj = glm.perspective(glm.radians(90.0), float(width) / float(height), 0.1, 15.0)

    half_fovy_tan = glm.tan(90.0 / 2.0)
    top = 0.1 * half_fovy_tan
    bottom = -top
    right = top * float(width) / float(height)
    left = -right
    orthoj = glm.ortho(left, right, bottom, top, 0.1, 15.0)

    view = glm.lookAt(viewPos, glm.vec3(0, 0, 0), glm.vec3(0, 0, 1))
    model = glm.mat4(1.0)
    # model = glm.rotate(model, glm.radians(time_count * 5), glm.vec3(0, 0, 1))

    mvp = proj * view * model

    return mvp, model, orthoj


def render():
    global shaderProgram
    global VAO

    glClearColor(0, 0, 0, 1)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    glDepthFunc(GL_LESS)
    glEnable(GL_DEPTH_TEST)

    glUseProgram(shaderProgram)

    mvp_mat, m_mat, ortho_mat = calc_mvp(640, 480)
    mvp_loc = glGetUniformLocation(shaderProgram, "MVP")
    glUniformMatrix4fv(mvp_loc, 1, GL_FALSE, glm.value_ptr(mvp_mat))
    m_loc = glGetUniformLocation(shaderProgram, "M_camera")
    glUniformMatrix4fv(m_loc, 1, GL_FALSE, glm.value_ptr(m_mat))
    lightPosLoc = glGetUniformLocation(shaderProgram, "lightPos")
    glUniform3f(lightPosLoc, *light)
    viewPosLoc = glGetUniformLocation(shaderProgram, "viewPos")
    glUniform3f(viewPosLoc, *viewPos)
    numTranLoc = glGetUniformLocation(shaderProgram, "num_tran")
    glUniform1i(numTranLoc, NumVertices // 3)
    spheretrangle_num = glGetUniformLocation(shaderProgram, "spheretriangle_num")
    glUniform1i(spheretrangle_num, numbers * (numbers) * 2)

    glBindVertexArray(VAO)
    glDrawArrays(GL_TRIANGLES, 0, NumVertices)

    glActiveTexture(GL_TEXTURE0)
    glUniform1i(glGetUniformLocation(shaderProgram, "triangleData"), 0)
    glActiveTexture(GL_TEXTURE1)
    glUniform1i(glGetUniformLocation(shaderProgram, "color"), 1)
    glActiveTexture(GL_TEXTURE2)
    glUniform1i(glGetUniformLocation(shaderProgram, "normal"), 2)
    glActiveTexture(GL_TEXTURE3)
    glUniform1i(glGetUniformLocation(shaderProgram, "child_info"), 3)
    glActiveTexture(GL_TEXTURE4)
    glUniform1i(glGetUniformLocation(shaderProgram, "box1"), 4)
    glActiveTexture(GL_TEXTURE5)
    glUniform1i(glGetUniformLocation(shaderProgram, "box2"), 5)
    glActiveTexture(GL_TEXTURE6)
    glUniform1i(glGetUniformLocation(shaderProgram, "samples"), 6)

    glutSwapBuffers()
    # 保存图片，但要等待完全渲染完才可以; 要保证图形框为当前主窗口
    # 也就是说弹出图片框后点一下渲染速度会快很多
    glPixelStorei(GL_PACK_ALIGNMENT, 1)
    data = glReadPixels(0, 0, window_x, window_y, GL_RGBA, GL_UNSIGNED_BYTE)
    image = Image.frombytes("RGBA", (window_x, window_y), data)
    image = ImageOps.flip(image)
    image.save('fig\glutout.png', 'PNG')

def main():
    global positions
    global normal
    global index
    glutInit([])

    cube_quad()
    print(index // 3)
    # node(0, 0, 0, 1)
    # node(-0.5, 0.5, -2, 1)
    # quad_sphere([1.0, 1.0, 1.0])
    # positions = []
    # normal = []
    # node(-0.2, 2.0, -2.02, 0.8)
    # quad_sphere([1.0, 1.0, 0.0])
    # print(index // 3)
    # positions = []
    # normal = []
    node(-1, -2, 0, 0.9)
    # quad_sphere([0.54, 0.84, 0.84])
    quad_sphere([1.5, 0.0, 1.0])
    print(index // 3)

    glutSetOption(GLUT_MULTISAMPLE, 8)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH | GLUT_MULTISAMPLE)
    glutInitWindowSize(window_x, window_y)
    glutCreateWindow("pyopengl with glut")
    initliaze()
    glutDisplayFunc(render)

    glutMainLoop()


if __name__ == '__main__':
    main()
