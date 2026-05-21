<template>
  <div>
    <el-row :gutter="16" style="margin-bottom: 20px">
      <el-col :span="6">
        <el-card shadow="hover">
          <div style="display: flex; align-items: center; justify-content: space-between">
            <div>
              <div style="color: #909399; font-size: 14px">代理状态</div>
              <div style="margin-top: 8px">
                <el-tag :type="proxyRunning ? 'success' : 'danger'" effect="dark" size="large">
                  {{ proxyRunning ? '运行中' : '已停止' }}
                </el-tag>
              </div>
            </div>
            <el-icon :size="40" :color="proxyRunning ? '#67c23a' : '#f56c6c'"><Connection /></el-icon>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div style="display: flex; align-items: center; justify-content: space-between">
            <div>
              <div style="color: #909399; font-size: 14px">总请求数</div>
              <div style="font-size: 28px; font-weight: bold; color: #409eff; margin-top: 8px">{{ stats.total_requests || 0 }}</div>
            </div>
            <el-icon :size="40" color="#409eff"><DataLine /></el-icon>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div style="display: flex; align-items: center; justify-content: space-between">
            <div>
              <div style="color: #909399; font-size: 14px">Token 消耗</div>
              <div style="font-size: 28px; font-weight: bold; color: #e6a23c; margin-top: 8px">{{ formatTokens(stats.total_tokens || 0) }}</div>
            </div>
            <el-icon :size="40" color="#e6a23c"><Coin /></el-icon>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div style="display: flex; align-items: center; justify-content: space-between">
            <div>
              <div style="color: #909399; font-size: 14px">成功率</div>
              <div style="font-size: 28px; font-weight: bold; color: #67c23a; margin-top: 8px">{{ successRate }}%</div>
            </div>
            <el-icon :size="40" color="#67c23a"><CircleCheck /></el-icon>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="hover">
      <template #header><span style="font-weight: bold">快速开始</span></template>
      <el-steps :active="proxyRunning ? 1 : 0" finish-status="success" align-center style="padding: 20px 0">
        <el-step title="启动代理" description="点击下方按钮启动 MITM 代理" />
        <el-step title="安装证书" description="到代理设置页下载并安装 CA 证书" />
        <el-step title="添加模型" description="到模型配置页添加 API Key" />
        <el-step title="开始使用" description="在 Cursor 使用你配置的模型" />
      </el-steps>
      <div style="text-align: center; margin-top: 20px">
        <el-button type="primary" size="large" @click="toggleProxy" :loading="loading">
          {{ proxyRunning ? '停止代理' : '启动代理' }}
        </el-button>
        <el-button size="large" @click="$router.push('/providers')">配置模型</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Connection, DataLine, Coin, CircleCheck } from '@element-plus/icons-vue'

const proxyRunning = ref(false)
const stats = ref({})
const loading = ref(false)

const successRate = computed(() => {
  const s = stats.value.success_count || 0
  const e = stats.value.error_count || 0
  return s + e === 0 ? 100 : Math.round((s / (s + e)) * 100)
})

function formatTokens(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K'
  return n
}

async function fetchAll() {
  try {
    const [h, s] = await Promise.all([
      axios.get('/api/proxy/status'),
      axios.get('/api/stats'),
    ])
    proxyRunning.value = h.data.running ?? false
    stats.value = s.data
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
    await fetchAll()
  } catch (e) {
    ElMessage.error('操作失败')
  } finally {
    loading.value = false
  }
}

onMounted(fetchAll)
</script>
