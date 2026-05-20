<template>
  <el-container style="height: 100vh">
    <el-aside width="220px" style="background: #304156">
      <div style="height: 60px; display: flex; align-items: center; justify-content: center; border-bottom: 1px solid #3c4f65">
        <span style="color: #409eff; font-size: 18px; font-weight: bold">Cursor Assistant</span>
      </div>
      <el-menu :default-active="activeMenu" router background-color="#304156" text-color="#bfcbd9" active-text-color="#409eff" style="border-right: none">
        <el-menu-item index="/">
          <el-icon><Monitor /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/providers">
          <el-icon><Cpu /></el-icon>
          <span>模型配置</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>代理设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header style="background: #fff; border-bottom: 1px solid #e6e6e6; display: flex; align-items: center; justify-content: space-between; padding: 0 20px; height: 60px">
        <span style="font-size: 16px; color: #303133">{{ pageTitle }}</span>
        <el-tag type="success" size="small">v1.0.0</el-tag>
      </el-header>
      <el-main style="background: #f0f2f5; padding: 20px">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Monitor, Cpu, Setting } from '@element-plus/icons-vue'

const route = useRoute()
const activeMenu = computed(() => route.path)
const titles = { '/': '仪表盘', '/providers': '模型配置', '/settings': '代理设置' }
const pageTitle = computed(() => titles[route.path] || 'Cursor Assistant')
</script>
