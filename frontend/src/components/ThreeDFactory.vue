<template>
    <div class="gltf-viewer">
        <TresCanvas v-bind="gl" ref="canvas">
            <TresPerspectiveCamera :position="[5, 5, 5]" :look-at="[0, 0, 0]" />

            <!-- 环境光 -->
            <TresAmbientLight :intensity="0.5" />

            <!-- 定向光 -->
            <TresDirectionalLight :position="[10, 10, 5]" :intensity="1" />

            <!-- GLTF模型 -->
            <Suspense>
                <GLTFModel v-if="modelUrl" :path="modelUrl" :scale="modelScale" :position="modelPosition"
                    :rotation="modelRotation" />
            </Suspense>

            <!-- 轨道控制器 -->
            <OrbitControls :enable-damping="true" :damping-factor="0.05" :min-distance="2" :max-distance="20" />
        </TresCanvas>

        <!-- 控制面板 -->
        <div class="controls">
            <div class="control-group">
                <label>模型URL：</label>
                <input v-model="modelUrl" type="text" placeholder="输入GLTF模型URL" class="url-input" />
            </div>

            <div class="control-group">
                <label>缩放：</label>
                <input v-model.number="modelScale" type="range" min="0.1" max="3" step="0.1" class="range-input" />
                <span>{{ modelScale }}</span>
            </div>

            <div class="control-group">
                <button @click="resetView" class="reset-btn">重置视角</button>
                <button @click="loadDefaultModel" class="load-btn">加载示例模型</button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { TresCanvas } from '@tresjs/core'
import {
    OrbitControls,
    GLTFModel
} from '@tresjs/cientos'

// 画布配置
const gl = reactive({
    clearColor: '#2c3e50',
    shadows: true,
    alpha: false,
    antialias: true
})

// 模型参数
const modelUrl = ref('https://threejs.org/examples/models/gltf/DamagedHelmet/glTF/DamagedHelmet.gltf')
const modelScale = ref(1)
const modelPosition = ref([0, 0, 0])
const modelRotation = ref([0, 0, 0])

// canvas引用
const canvas = ref()

// 重置视角
const resetView = () => {
    modelScale.value = 1
    modelPosition.value = [0, 0, 0]
    modelRotation.value = [0, 0, 0]
}

// 加载默认模型
const loadDefaultModel = () => {
    modelUrl.value = 'https://threejs.org/examples/models/gltf/DamagedHelmet/glTF/DamagedHelmet.gltf'
    resetView()
}
</script>

<style scoped>
.gltf-viewer {
    position: relative;
    width: 100%;
    height: 100vh;
    overflow: hidden;
}

.controls {
    position: absolute;
    top: 20px;
    left: 20px;
    background: rgba(0, 0, 0, 0.8);
    backdrop-filter: blur(10px);
    padding: 20px;
    border-radius: 12px;
    color: white;
    font-size: 14px;
    min-width: 300px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.control-group {
    margin-bottom: 15px;
    display: flex;
    align-items: center;
    gap: 10px;
}

.control-group label {
    min-width: 60px;
    font-weight: 500;
}

.url-input {
    flex: 1;
    padding: 8px 12px;
    border: none;
    border-radius: 6px;
    background: rgba(255, 255, 255, 0.1);
    color: white;
    outline: none;
    transition: background 0.3s ease;
}

.url-input:focus {
    background: rgba(255, 255, 255, 0.2);
}

.url-input::placeholder {
    color: rgba(255, 255, 255, 0.6);
}

.range-input {
    flex: 1;
    margin-right: 10px;
}

.reset-btn,
.load-btn {
    padding: 8px 16px;
    border: none;
    border-radius: 6px;
    background: #3498db;
    color: white;
    cursor: pointer;
    font-weight: 500;
    transition: background 0.3s ease;
    margin-right: 10px;
}

.reset-btn:hover,
.load-btn:hover {
    background: #2980b9;
}

.load-btn {
    background: #27ae60;
}

.load-btn:hover {
    background: #229954;
}
</style>
  
