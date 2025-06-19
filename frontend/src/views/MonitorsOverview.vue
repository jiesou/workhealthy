<template>
    <div class="overview-container">
        <h1>监控总览</h1>
        <div class="camera-grid">
            <div v-for="camera in eventBus.monitorList" :key="camera" class="camera-item">
                <h6>{{ camera }}</h6>
                <img :src="`http://localhost:5173/api/monitor/${encodeMonitorUrl(String(camera))}/video_feed`"
                    alt="视频监控" class="video-feed">
            </div>
        </div>
        <ThreeDFactory />
    </div>
</template>

<script setup>
import { computed } from 'vue';
import eventBus from '@/services/eventBus';
import { encodeMonitorUrl } from '@/services/api';

import ThreeDFactory from '@/components/ThreeDFactory.vue';

</script>

<style scoped>
.overview-container {
    display: flex;
    flex-direction: column;
    height: 100vh;
    padding: 2rem;
}

.camera-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
}

.camera-item {
    border: 1px solid #ccc;
    padding: 1rem;
    text-align: center;
}

.video-feed {
    width: 100%;
    height: auto;
}

/* 确保3D工厂占据剩余空间 */
.overview-container > :last-child {
    flex: 1;
    min-height: 400px;
}
</style>