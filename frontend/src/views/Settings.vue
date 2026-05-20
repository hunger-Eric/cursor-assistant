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
            <el-button type="primary" @click="toggleProxy" :loading="loading">{{ proxyRunning ? '停止代理' : '启动代理' }}</el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header><span style="font-weight: bold">CA 证书</span></template>
          <el-alert v-if="!proxyRunning" type="warning" :closable="false" show-icon title="请先启动代理再下载证书" style="margin-bottom: 16px" />
          <div v-else>
            <p style="color: #606266; margin-bottom: 16px">安装 CA 证书后，代理才能解密 HTTPS 流量</p>
            <el-button type="success" @click="downloadCert">
              <el-icon><Download /></el-icon> 下载 CA 证书
            </el-button>
          </div>
          <el-divider />
          <div>
            <p style="color: #606266; font-size: 13px"><strong>Windows 安装步骤：</strong></p>
            <ol style="color: #909399; font-size: 13px; padding-left: 18px; line-height: 1.8">
              <li>双击下载的 .pem 文件</li>
              <li>点击"安装证书"</li>
              <li>选择"本地计算机" - 下一步</li>
              <li>选择"将所有证书放入下列存储" - 浏览</li>
              <li>选择"受信任的根证书颁发机构" - 确定</li>
              <li>完成安装</li>
            </ol>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="hover" style="margin-top: 16px">
      <template #header><span style="font-weight: bold">系统代理设置</span></template>
      <el-alert type="info" :closable="false" show-icon>
        <template #title>将系统 HTTP/HTTPS 代理设置为 <strong>127.0.0.1:8080</strong>，然后重启 Cursor IDE 即可使用国产模型</template>
      </el-alert>
      <el-descriptions :column="1" border style="margin-top: 16px">
        <el-descriptions-item label="HTTP 代理">127.0.0.1:8080</el-descriptions-item>
        <el-descriptions-item label="HTTPS 代理">127.0.0.1:8080</el-descriptions-item>
        <el-descriptions-item label="排除地址">localhost; 127.0.0.1; *.cursor.sh</el-descriptions-item>
      </el-descriptions>
      <el-divider content-position="left">Windows 设置方法</el-divider>
      <ol style="color: #606266; font-size: 13px; padding-left: 18px; line-height: 2">
        <li>打开 <strong>设置 - 网络和 Internet - 代理</strong></li>
        <li>在"手动设置代理"中开启"使用代理服务器"</li>
        <li>代理地址填 <strong>127.0.0.1</strong>，端口填 <strong>8080</strong></li>
        <li>在"请勿对以下条目开头的地址使用代理服务器"中填入 <strong>localhost;127.0.0.1;*.cursor.sh</strong></li>
        <li>点击保存，重启 Cursor</li>
      </ol>
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
  try { const res = await axios.get('/api'); proxyRunning.value = res.data.proxy_running ?? false } catch (e) { console.error(e) }
}

async function toggleProxy() {
  loading.value = true
  try {
    const url = proxyRunning.value ? '/api/proxy/stop' : '/api/proxy/start'
    await axios.get(url)
    ElMessage.success(proxyRunning.value ? '代理已停止' : '代理已启动')
    await fetchStatus()
  } catch (e) { ElMessage.error('操作失败') }
  finally { loading.value = false }
}

function downloadCert() {
  const a = document.createElement('a')
  a.href = 'http://localhost:8000/certs/download'
  a.download = 'mitmproxy-ca-cert.pem'
  a.click()
  ElMessage.success('证书下载中...')
}

onMounted(fetchStatus)
</script>
