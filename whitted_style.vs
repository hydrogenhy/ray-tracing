#version 410

    layout(location = 0) in vec4 position;
    uniform mat4 MVP;
    out vec3 pos;
    
    void main() {
        gl_Position = MVP * position;
        pos = vec3(position);
    } 