<template>
    <div class="factory-container">
        <TresCanvas class="three-canvas">
            <TresPerspectiveCamera :position="[1, 1, 1]" />
            <OrbitControls />
            
            <TresAmbientLight :intensity="0.6" />
            <TresDirectionalLight :position="[2, 2, 2]" :intensity="0.8" />
            
            <!-- 测试立方体 -->
            <TresMesh :position="[0, 0, 0]">
                <TresBoxGeometry :args="[0.1, 0.1, 0.1]" />
                <TresMeshStandardMaterial color="hotpink" />
            </TresMesh>
            
            <!-- GLTF模型 -->
            <primitive v-if="loadedModel" :object="loadedModel" />
        </TresCanvas>
        
        <div v-if="!modelLoaded && !modelError" class="loading-indicator">
            加载3D模型中...
        </div>
        
        <div v-if="modelError" class="error-indicator">
            模型加载失败: {{ modelError }}
        </div>
    </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { TresCanvas } from '@tresjs/core'
import { OrbitControls } from '@tresjs/cientos'
import { Box3, Vector3 } from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader.js'
import { useTresContext } from '@tresjs/core'

const modelLoaded = ref(false)
const modelError = ref(null)
const testLoad = ref(false)
const canvasRef = ref()
const loadedModel = ref(null)

const onLoad = (model) => {
    console.log("模型加载成功!", model)
    modelLoaded.value = true
    
    // 计算模型的包围盒和中心位置
    const box = new Box3().setFromObject(model)
    const center = box.getCenter(new Vector3())
    const size = box.getSize(new Vector3())
    console.log('模型中心:', center)
    console.log('模型尺寸:', size)
}

const onError = (error) => {
    console.error("模型加载失败:", error)
    modelError.value = error.message || error
}

// 手动测试GLTF加载
const testGLTFLoad = () => {
    const loader = new GLTFLoader()
    
    // 设置DRACOLoader
    const dracoLoader = new DRACOLoader()
    dracoLoader.setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.6/')
    loader.setDRACOLoader(dracoLoader)
    
    console.log("开始手动加载GLTF...")
    
    loader.load(
        '/factory.gltf',
        (gltf) => {
            console.log('手动加载成功:', gltf)
            testLoad.value = true
            
            // 存储模型供模板使用
            loadedModel.value = gltf.scene
            
            // 计算模型尺寸并调整位置
            const model = gltf.scene
            const box = new Box3().setFromObject(model)
            const center = box.getCenter(new Vector3())
            const size = box.getSize(new Vector3())
            
            console.log('模型中心:', center)
            console.log('模型尺寸:', size)
            
            // 将模型居中并缩放
            model.position.set(-center.x, -center.y - 5, -center.z) // 向下移动
            
            // 如果模型太大，缩放它
            const maxSize = Math.max(size.x, size.y, size.z)
            if (maxSize > 10) {
                const scale = 10 / maxSize
                model.scale.set(scale, scale, scale)
                console.log('模型已缩放:', scale)
            }
            
            modelLoaded.value = true
            console.log('模型准备就绪')
        },
        (progress) => {
            console.log('加载进度:', progress)
        },
        (error) => {
            console.error('手动加载失败:', error)
            modelError.value = error.message || error
        }
    )
}

onMounted(() => {
    console.log("ThreeDFactory组件已挂载")
    
    // 等待一帧后再开始加载，确保canvas已经初始化
    setTimeout(() => {
        // 检查factory.gltf是否可访问
        fetch('/factory.gltf')
            .then(response => {
                if (response.ok) {
                    console.log("factory.gltf文件可访问, Content-Type:", response.headers.get('content-type'))
                    testGLTFLoad() // 手动测试加载
                } else {
                    console.error("factory.gltf文件不可访问:", response.status)
                }
            })
            .catch(error => {
                console.error("检查factory.gltf时出错:", error)
            })
    }, 100)
})
</script>
<style scoped>
.factory-container {
    position: relative;
    width: 100%;
    height: 100%;
    min-height: 400px;
}

.three-canvas {
    width: 100%;
    height: 100%;
    background-color: darkgrey;
}

.loading-indicator,
.error-indicator {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    padding: 1rem 2rem;
    background-color: rgba(0, 0, 0, 0.7);
    color: white;
    border-radius: 8px;
    z-index: 10;
}

.error-indicator {
    background-color: rgba(220, 53, 69, 0.9);
}
</style>