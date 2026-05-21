<template>
  <div>
    <el-row :gutter="16">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header><span style="font-weight: bold">代理配置</span></template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="监听地址">127.0.0.1</el-descriptions-item>
            <el-descriptions-item label="监听端口">8080</el-descriptions-item>
            <el-descriptions-item label="当前状态">
              <el-tag :type="proxyRunning ? 'success' : 'danger'">{{ proxyRunning ? '运行中' : '已停止' }}</el-tag>
            </el-descriptions-item>
          </el-descriptions>
          <div style="margin-top: 20px">
            <el-button type="primary" @click="toggleProxy" :loading="loading">
              {{ proxyRunning ? '停止代理' : '启动代理' }}
            </el-button>
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card shadow="hover">
          <template #header><span style="font-weight: bold">CA 证书</span></template>
          <el-alert
            v-if="!proxyRunning"
            type="warning"
            :closable="false"
            show-icon
            title="请先启动代理再下载证书"
            style="margin-bottom: 16px"
          />
          <div v-else>
            <p style="color: #606266; margin-bottom: 16px">安装 CA 证书后，代理才能解密 HTTPS 流量</p>
            <el-button type="success" @click="downloadCert">
              <el-icon><Download /></el-icon> 下载 CA 证书
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="hover" style="margin-top: 16px">
      <template #header><span style="font-weight: bold">系统代理设置</span></template>
      <el-alert type="info" :closable="false" show-icon>
        <template #title>将系统 HTTP/HTTPS 代理设置为 <strong>127.0.0.1:8080</strong>，然后重启 Cursor。</template>
      </el-alert>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'

const proxyRunning = ref(false)
const loading = ref(false)

async function fetchStatus() {
  try {
    const res = await axios.get('/api/proxy/status')
    proxyRunning.value = res.data.running ?? false
  } catch (e) {
    console.error(e)
  }
}

async function toggleProxy() {
  loading.value = true
  try {
    const url = proxyRunning.value ? '/api/proxy/stop' : '/api/proxy/start'
    await axios.get(url)
    ElMessage.success(proxyRunning.value ? '代理已停止' : '代理已启动')
    await fetchStatus()
  } catch (e) {
    ElMessage.error('操作失败')
  } finally {
    loading.value = false
  }
}

function downloadCert() {
  window.open('/api/proxy/cert', '_blank')
  ElMessage.success('证书下载中...')
}

onMounted(fetchStatus)
</script>
