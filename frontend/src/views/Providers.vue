<template>
  <div>
    <el-card shadow="hover">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span style="font-weight: bold">模型提供商</span>
          <el-button type="primary" @click="openDialog()">
            <el-icon><Plus /></el-icon> 添加提供商
          </el-button>
        </div>
      </template>

      <el-empty v-if="providers.length === 0" description="暂无模型配置，点击上方按钮添加" />

      <el-table v-else :data="providers" stripe style="width: 100%">
        <el-table-column prop="name" label="名称" width="140" />
        <el-table-column prop="type" label="类型" width="130">
          <template #default="{ row }">
            <el-tag size="small">{{ typeMap[row.type] || row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="base_url" label="API 地址" show-overflow-tooltip />
        <el-table-column label="模型" width="100">
          <template #default="{ row }">{{ row.models?.length || 0 }} 个</template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" type="primary" plain @click="testProvider(row)">测试</el-button>
            <el-button size="small" type="danger" plain @click="deleteProvider(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑提供商' : '添加提供商'" width="520px" destroy-on-close>
      <el-form :model="form" label-width="100px" :rules="rules" ref="formRef">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="例如: 我的 DeepSeek" />
        </el-form-item>
        <el-form-item label="类型" prop="type">
          <el-select v-model="form.type" placeholder="选择模型类型" @change="onTypeChange" style="width: 100%">
            <el-option label="DeepSeek" value="deepseek" />
            <el-option label="通义千问 (Qwen)" value="qwen" />
            <el-option label="智谱 GLM" value="glm" />
            <el-option label="Kimi (Moonshot)" value="kimi" />
          </el-select>
        </el-form-item>
        <el-form-item label="API Key" prop="api_key">
          <el-input v-model="form.api_key" type="password" show-password placeholder="输入你的 API Key" />
        </el-form-item>
        <el-form-item label="API 地址" prop="base_url">
          <el-input v-model="form.base_url" placeholder="留空使用默认地址" />
        </el-form-item>
        <el-form-item label="模型 ID" prop="model_id">
          <el-input v-model="form.model_id" placeholder="留空使用默认模型" />
        </el-form-item>
        <el-form-item label="模型名称">
          <el-input v-model="form.model_name" placeholder="显示名称，留空自动生成" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const providers = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref(null)

const typeMap = { deepseek: 'DeepSeek', qwen: '通义千问', glm: '智谱 GLM', kimi: 'Kimi' }
const defaultUrls = { deepseek: 'https://api.deepseek.com/v1', qwen: 'https://dashscope.aliyuncs.com/compatible-mode/v1', glm: 'https://open.bigmodel.cn/api/paas/v4', kimi: 'https://api.moonshot.cn/v1' }
const defaultModels = { deepseek: 'deepseek-chat', qwen: 'qwen-plus', glm: 'glm-4', kimi: 'moonshot-v1-8k' }
const defaultNames = { deepseek: 'DeepSeek V3', qwen: '通义千问 Plus', glm: 'GLM-4', kimi: 'Kimi 8K' }

const form = ref({ name: '', type: 'deepseek', api_key: '', base_url: '', model_id: '', model_name: '' })
const rules = { name: [{ required: true, message: '请输入名称', trigger: 'blur' }], type: [{ required: true, message: '请选择类型', trigger: 'change' }], api_key: [{ required: true, message: '请输入 API Key', trigger: 'blur' }] }

function onTypeChange() {
  form.value.base_url = defaultUrls[form.value.type] || ''
  form.value.model_id = defaultModels[form.value.type] || ''
  form.value.model_name = defaultNames[form.value.type] || ''
}

function openDialog() {
  isEdit.value = false
  form.value = { name: '', type: 'deepseek', api_key: '', base_url: defaultUrls.deepseek, model_id: defaultModels.deepseek, model_name: defaultNames.deepseek }
  dialogVisible.value = true
}

async function fetchProviders() {
  try { const res = await axios.get('/api/providers'); providers.value = res.data } catch (e) { console.error(e) }
}

async function submitForm() {
  try { await formRef.value.validate() } catch { return }
  submitting.value = true
  try {
    await axios.post('/api/providers', {
      name: form.value.name,
      type: form.value.type,
      api_key: form.value.api_key,
      base_url: form.value.base_url || defaultUrls[form.value.type],
      models: [{ model_id: form.value.model_id || defaultModels[form.value.type], name: form.value.model_name || defaultNames[form.value.type] }]
    })
    ElMessage.success('添加成功')
    dialogVisible.value = false
    fetchProviders()
  } catch (e) { ElMessage.error('添加失败: ' + (e.response?.data?.detail || e.message)) }
  finally { submitting.value = false }
}

async function deleteProvider(id) {
  try {
    await ElMessageBox.confirm('确定删除此模型配置？', '提示', { type: 'warning' })
    await axios.delete('/api/providers/' + id)
    ElMessage.success('已删除')
    fetchProviders()
  } catch (e) { if (e !== 'cancel') ElMessage.error('删除失败') }
}

async function testProvider(row) {
  ElMessage.info('正在测试连接...')
  try {
    const res = await axios.post('/api/providers/test', { provider_id: row.id })
    ElMessage.success('连接成功! 延迟: ' + res.data.latency_ms + 'ms')
  } catch (e) { ElMessage.error('连接失败: ' + (e.response?.data?.detail || e.message)) }
}

onMounted(fetchProviders)
</script>
