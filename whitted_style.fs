#version 410
    in vec3 pos;

    const int Ture = 1;
    const int False = 0;
    const int sphereID = 10000;

    uniform samplerBuffer triangleData;
    uniform samplerBuffer color;
    uniform samplerBuffer normal;
    uniform samplerBuffer child_info;
    uniform samplerBuffer box1;
    uniform samplerBuffer box2;
    uniform samplerBuffer samples;
    
    uniform vec3 viewPos;
    uniform vec3 lightPos;
    uniform mat4 M_camera;
    uniform int num_tran;
    uniform int spheretriangle_num;

    vec4 light_color = vec4(0.8, 0.8, 0.8, 1.0);
    
    #define MAX_STACK_SIZE 500
    int stack[MAX_STACK_SIZE];
    int top = -1;

    // 入栈操作
    void push(int vertex) {
        if (top < MAX_STACK_SIZE - 1) {
            stack[++top] = vertex;
        }
    }
    
    // 出栈操作
    int pop() {
        if (top >= 0) {
            return stack[top--];
        }
    }
    
    struct HitData
    {
        int tranID;
        float t;
        vec3 attach;
        vec3 reflection;  // 反射方向
        vec3 norm;
    };

    struct Ray
    {
        vec3 o;
        vec3 d; 
        float rate;  // 占比，用于平衡折射和反射
        int deepth;  // 迭代深度
        float light; // 光强
    };
    int ray_count = -1;
    Ray ray_stack[100];
    void push_ray(Ray vertex) {
        if (top < 100 - 1) {
            ray_stack[++ray_count] = vertex;
        }
    }
    Ray pop_ray() {
        if (ray_count >= 0) {
            return ray_stack[ray_count--];
        }
    }

    HitData hitSphere(vec3 center, float r, int sphere_now, vec3 o, vec3 d)  // 判断与球相交
    {
        HitData tmp;
        tmp.t = -1, tmp.tranID = -1;
        float a = dot(d, d);
        float b = 2 * dot(o - center, d);
        float c = dot(o - center, o - center) - r * r;
        float delta = b * b - 4 * a * c;
        if(delta < 0)
            return tmp;
        float t1 = (-b - sqrt(delta)) / (2 * a), t2 = (-b - sqrt(delta)) / (2 * a);
        float t0 = 0;
        if(abs(delta) < 1e-6)
            t0 = t1;
        else
        {
            if(t1 < 0)
                t0 = t2;
            else
                t0 = t1;
        }

        if(t0 > 0)
        {
            tmp.t = t0;
            tmp.tranID = sphereID + sphere_now;
            tmp.attach = o + t0 * d;
            tmp.norm = normalize(tmp.attach - center);
            tmp.reflection = reflect(d, tmp.norm);
        }

        return tmp;
    }
    
    HitData check(vec3 o, vec3 d, vec3 V1, vec3 V2, vec3 V3, int tranID)  // 判断光线是否打到在三角形内
    {
        HitData res;
        res.t = -1, res.attach = vec3(0, 0, 0), res.tranID = -1;
        vec3 norm = normalize(cross(V3 - V1, V2 - V1)); // vec3(texelFetch(normal, tranID * 3)); //
        float t = - dot(o - V1, norm) / (dot(d, norm) + 1e-6);
        vec3 x = o + t * d;
        float S1 = dot(cross(x - V1, V2 - V1), norm);
        float S2 = dot(cross(x - V3, V1 - V3), norm);
        float S3 = dot(cross(x - V2, V3 - V2), norm);
        if(sign(S1) == sign(S2) && sign(S3) == sign(S2))  // 混合积大于0
        {
            res.t = t, res.attach = x, res.tranID = tranID;
            res.norm = norm, res.reflection = reflect(normalize(d) ,norm);
        }
        return res;
    }
    
    HitData hitbox(vec3 o, vec3 d)  // 是否打到最外层的正方体边界
    {
        HitData tmp;
        tmp.t = -9999999;
        int i;
        for(i = 0; i < 12; i ++)
        {
            HitData tt;
            tt = check(o, d, vec3(texelFetch(triangleData, i * 3 + 0)), 
                        vec3(texelFetch(triangleData, i * 3 + 1)), vec3(texelFetch(triangleData, i * 3 + 2)), i);
            if(tt.t > 0 && tt.t < abs(tmp.t))
            {
                tmp = tt;
            }
        }
        return tmp;
    }
    
    float hit(vec3 o, vec3 d, int ID)  // 是否经过aabb盒
    {
        int i;
        vec3 bbox1 = vec3(texelFetch(box1, ID));
        vec3 bbox2 = vec3(texelFetch(box2, ID));
        float t_min = -99999999.0, t_max = 99999999.0;
        for(i = 0; i < 3; i ++)
        {
            float t0 = (bbox1[i] - o[i]) / (d[i]);  // min
            float t1 = (bbox2[i] - o[i]) / (d[i]);  // max
            if (d[i] < 0.0f)
            {
                float z = t0;
                t0 = t1, t1 = z;
            }
            t_min = t0 > t_min ? t0 : t_min;
            t_max = t1 < t_max ? t1 : t_max;
            if(t_min > t_max)  
                return -1.0;
        }
        return 1.0;
    }
    
    HitData find_BVH(vec3 o, vec3 d)  // 通过BVH快速查找三角形范围
    {
        top = -1;
        HitData tmp;
        tmp.t = -999999, tmp.tranID = -1;
        int now_ID = 0, i;
        push(0);
        while(top >= 0)
        {
            now_ID = pop();
            if(texelFetch(child_info, now_ID).x < 1e-6)
            {
                for(i = 0; i < 4; i ++)
                {
                    int tranID = int(texelFetch(samples, now_ID)[i] + 0.1);
                    if(tranID > 0)
                    {
                        HitData tt;
                        tt = check(o, d, vec3(texelFetch(triangleData, tranID * 3 + 0)), 
                                    vec3(texelFetch(triangleData, tranID * 3 + 1)), vec3(texelFetch(triangleData, tranID * 3 + 2)), tranID);
                        if(tt.t > 0 && tt.t < abs(tmp.t))
                        {
                            tmp = tt;
                        }
                    }
                }
            }
            else
            {
                float left_t = hit(o, d, int(texelFetch(child_info, now_ID).x + 0.1));
                float right_t = hit(o, d, int(texelFetch(child_info, now_ID).y + 0.1));
                if(left_t > 0 && right_t > 0)
                {
                    push(int(texelFetch(child_info, now_ID).x + 0.1));
                    push(int(texelFetch(child_info, now_ID).y + 0.1));
                }
                else if(left_t < 0 && right_t > 0)
                {
                    push(int(texelFetch(child_info, now_ID).y + 0.1));
                }
                else if(left_t > 0 && right_t < 0)
                {
                    push(int(texelFetch(child_info, now_ID).x + 0.1));
                }
            }
        }
        return tmp;
    }
    
    
    HitData Interaction(vec3 o, vec3 d)  // 得到光线击中物体的信息
    {
        int i;
        HitData tmp = find_BVH(o, d);
        HitData worldbox = hitbox(o, d);
        if(worldbox.t > 0 && tmp.tranID < 12)
            tmp = worldbox;
        HitData sphere = hitSphere(vec3(0, 0, 30 + 4), 30.015, 0, o, d); // light
        if(sphere.t > 0 && sphere.t < tmp.t)
            tmp = sphere;
        sphere = hitSphere(vec3(-0.8, 0, 1), 0.8, 1, o, d);
        if(sphere.t > 0 && sphere.t < tmp.t)
            tmp = sphere;
        sphere = hitSphere(vec3(-0.2, 2.0, -2.02), 0.7, 2, o, d);
        if(sphere.t > 0 && sphere.t < tmp.t)
            tmp = sphere;

        return tmp;
    }

    int shadow_check(vec3 o, vec3 d)
    {
        HitData shadow = Interaction(o, d);
        if((shadow.t < 1) && (shadow.t > 0))
            return Ture;
        return False;
    }

    vec3 refraction(vec3 I, vec3 N, float ior)
    {
        I = normalize(I);
        N = normalize(N);
        float cosi = dot(I, N);
        float etai = 1, etat = ior;  //1为空气折射率，ior为介质的折射率,水1.33
        vec3 n = N;
        //如果入射光从介质1(etai)->介质2(etat)，则夹角>90°；
        //如果入射光从介质2->介质1，则夹角<90,N也要反过来，折射率之比也需要换一下
        if (cosi < 0)
        {
            cosi = -cosi;
        }
        else
        {
            float tmp_e = etai;
            etai = etat;
            etat = etai;
            n = -N;
        }
        float eta = etai / etat;
        float k = 1 - eta * eta * (1 - cosi * cosi);
        if(k < 0)  // 全反射
            return vec3(0);
        return eta * I + (eta * cosi - sqrt(k)) * n;
    }

    float fresnel(vec3 I, vec3 N, float ior)
    {
        I = normalize(I);
        N = normalize(N);
        float cosi = dot(I, N);
        float etai = 1, etat = ior;
        if(cosi > 0)
        {
            float tmp_e = etai;
            etai = etat;
            etat = etai;
        }
        // Compute sini using Snell's law 即：sin比等于折射率反比
        float sint = etai / etat * sqrt(max(0.f, 1 - cosi * cosi));
        // Total internal reflection，全反射
        if (sint >= 1) {
            return 1.0;
        }
        else {
            //cos²+sin²=1
            float cost = sqrt(max(0.f, 1 - sint * sint));
            cosi = abs(cosi);
            float Rs = ((etat * cosi) - (etai * cost)) / ((etat * cosi) + (etai * cost));
            float Rp = ((etai * cosi) - (etat * cost)) / ((etai * cosi) + (etat * cost));
            return (Rs * Rs + Rp * Rp) / 2;
        }
    }

    
    vec4 cast_ray_Phone(float lightIntensity, float kd, float ks, int pow_num, HitData tmp)
    {
        if(tmp.tranID == sphereID)
            return light_color * lightIntensity;
        vec4 piexl_color = vec4(0);
        vec3 shadow_d = lightPos - tmp. attach;
        vec3 shadow_o = tmp.attach + 1e-4 * shadow_d;

        vec4 ambint = 0.1 * lightIntensity * texelFetch(color, tmp.tranID * 3);

        int inshadow = shadow_check(shadow_o, shadow_d);

        float dist = dot(lightPos - tmp.attach, lightPos - tmp.attach);

        vec4 diffuse = (1 - inshadow) * lightIntensity * light_color/ dist * max(dot(tmp.norm, normalize(lightPos - tmp.attach)), 0.0) * texelFetch(color, tmp.tranID * 3);
        vec4 specular = (1 - inshadow) * lightIntensity * light_color / dist * pow(max(dot(normalize(lightPos - tmp.attach), tmp.reflection), 0.0), pow_num) * texelFetch(color, tmp.tranID * 3);
        
        return ambint + diffuse * kd + specular * ks;
    }

    int getMaterial(int ID)
    {
        //  || ID == 0 || ID == 1  || ID == 2 || ID == 3  // mirror
        if(ID == sphereID + 1) // 一个sphere是 mirror ball
            return 1;
        else if(ID == sphereID + 2)  // 一个sphere是glass ball
            return 2;
        // 其它漫反射材质
        else if(ID >=  12)
            return 3;
        return 4;
    }
    
    void main() {
        int count_debug = 0;
        float ka = 0.2, kd = 10, ks = 50;
        float reduction = 0.1;
        float lightIntensity = 3.0;
        vec4 tmp_color = vec4(0.0f, 0.0f, 0.0f, 1.0f);
        int i = 0, k;
        vec3 o = viewPos;
        vec3 d = pos - viewPos;
        Ray ray_tmp;
        ray_tmp.o = o, ray_tmp.d = d, ray_tmp.rate = 1.0;
        ray_tmp.deepth = 0, ray_tmp.light = lightIntensity;
        int MAX_DEEP = 8;
        push_ray(ray_tmp);
        while(ray_count >= 0){
            Ray ray_now = pop_ray();
            o = ray_now.o;
            d = ray_now.d;
            vec4 ray_color = vec4(0.0f, 0.0f, 0.0f, 1.0f);
            HitData tmp = Interaction(o, d);
            
            if(tmp.tranID == sphereID && ray_now.deepth == 0)
            {
                tmp_color = light_color * ray_now.light;
                break;
            }

            if(tmp.tranID >= 0)
            {
                int material = getMaterial(tmp.tranID);
                if(material == 1)
                {
                    ray_tmp.d = tmp.reflection;
                    ray_tmp.o = tmp.attach + 1e-4 * ray_tmp.d;
                    ray_tmp.light = ray_now.light;
                    ray_tmp.rate = ray_now.rate;
                    ray_tmp.deepth = ray_now.deepth + 1;
                    if(ray_tmp.deepth < MAX_DEEP)
                        push_ray(ray_tmp);
                }

                else if(material == 2)
                {
                    d = refraction(d, tmp.norm, 1.33);
                    float fresnel_rate = fresnel(d, tmp.norm, 1.33);
                    if(length(d) > 1e-6)
                    {
                        // ray_color = cast_ray_Phone(ray_now.light, 1, 20, 128, tmp);
                        ray_tmp.d = d;
                        ray_tmp.o = tmp.attach + 1e-4 * ray_tmp.d;
                        ray_tmp.rate = ray_now.rate * (1 - fresnel_rate);
                        ray_tmp.deepth = ray_now.deepth + 1;
                        ray_tmp.light = ray_now.light;
                        if(ray_tmp.deepth < MAX_DEEP)
                            push_ray(ray_tmp);
                        // tmp_color += ray_color * 0.1;
                    }
                    ray_tmp.d = tmp.reflection;
                    ray_tmp.o = tmp.attach + 1e-4 * ray_tmp.d;
                    ray_tmp.rate = ray_now.rate * fresnel_rate;
                    ray_tmp.deepth = ray_now.deepth + 1;
                    ray_tmp.light = ray_now.light;
                    if(ray_tmp.deepth < MAX_DEEP)
                        push_ray(ray_tmp);
                }

                else if(material == 3)
                {
                    ray_color = cast_ray_Phone(ray_now.light, 25, 100, 128, tmp);
                    ray_tmp.d = tmp.reflection;
                    ray_tmp.o = tmp.attach + 1e-4 * ray_tmp.d;
                    ray_tmp.light = ray_now.light * reduction * 6;
                    ray_tmp.rate = ray_now.rate;
                    ray_tmp.deepth = ray_now.deepth + 1;
                    if(ray_tmp.deepth < MAX_DEEP)
                        push_ray(ray_tmp);
                    tmp_color += ray_color * ray_now.rate;

                }

                else if(material == 4)
                {
                    ray_color = cast_ray_Phone(ray_now.light, 10, 5, 64, tmp);
                    ray_tmp.d = tmp.reflection;
                    ray_tmp.o = tmp.attach + 1e-4 * ray_tmp.d;
                    ray_tmp.light = ray_now.light * reduction;
                    ray_tmp.rate = ray_now.rate;
                    ray_tmp.deepth = ray_now.deepth + 1;
                    tmp_color += ray_color * ray_now.rate;
                    continue;
                    if(ray_tmp.deepth < MAX_DEEP)
                        push_ray(ray_tmp);
                }

            }
            // count_debug ++;
            // if(count_debug > 5)
            //     break;
        }
        
        gl_FragColor = tmp_color;
    }
    